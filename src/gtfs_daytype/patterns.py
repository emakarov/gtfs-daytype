"""Build stable Route Pattern keys from ordered GTFS stop sequences."""

import hashlib
from collections import defaultdict

import h3

from gtfs_daytype.models import RoutePattern


def build_route_patterns(
    trips: list[dict[str, str]],
    stop_times: list[dict[str, str]],
    stops: list[dict[str, str]],
    *,
    h3_resolution: int = 15,
    key_method: str = 'h3',
) -> dict[str, RoutePattern]:
    """Build a Route Pattern for each trip from its ordered stop sequence.

    :param trips: Rows from ``trips.txt``.
    :param stop_times: Rows from ``stop_times.txt``.
    :param stops: Rows from ``stops.txt``.
    :param h3_resolution: H3 resolution used for coordinate-based keys.
    :param key_method: ``h3`` for H3 keys or ``stop_ids`` for direct stop-id keys.
    :returns: Mapping from ``trip_id`` to Route Pattern.
    """

    stops_by_id = {row['stop_id']: row for row in stops}
    stop_times_by_trip: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in stop_times:
        stop_times_by_trip[row['trip_id']].append(row)

    patterns_by_trip: dict[str, RoutePattern] = {}
    for trip in trips:
        trip_id = trip['trip_id']
        rows = sorted(
            stop_times_by_trip.get(trip_id, []),
            key=lambda row: int(row.get('stop_sequence', '0')),
        )
        stop_ids = tuple(row['stop_id'] for row in rows)
        if key_method == 'stop_ids':
            cells = stop_ids
        elif key_method == 'h3':
            cells = tuple(_stop_cell(stops_by_id[stop_id], h3_resolution) for stop_id in stop_ids)
        else:
            raise ValueError('key_method must be "h3" or "stop_ids"')

        key = _stable_key(cells)
        patterns_by_trip[trip_id] = RoutePattern(key=key, stop_ids=stop_ids, cells=cells)

    return patterns_by_trip


def _stop_cell(stop: dict[str, str], resolution: int) -> str:
    """Return the H3 cell for a GTFS stop row.

    :param stop: Row from ``stops.txt``.
    :param resolution: H3 resolution.
    :returns: H3 cell string.
    """
    return h3.latlng_to_cell(float(stop['stop_lat']), float(stop['stop_lon']), resolution)


def _stable_key(values: tuple[str, ...]) -> str:
    """Build a compact deterministic key for an ordered sequence.

    :param values: Ordered sequence values.
    :returns: Stable Route Pattern key.
    """
    payload = '|'.join(values)
    digest = hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]
    return f'rp_{digest}'
