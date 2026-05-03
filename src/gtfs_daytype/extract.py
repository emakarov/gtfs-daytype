"""Extract recurring DayTypes directly from GTFS files."""

from collections import defaultdict
from pathlib import Path

from gtfs_daytype.calendar import service_dates
from gtfs_daytype.io import read_gtfs_table
from gtfs_daytype.models import DayType, DayTypeResult, TripSpec
from gtfs_daytype.patterns import build_route_patterns
from gtfs_daytype.time import parse_gtfs_time


def extract_daytypes(
    gtfs_path: str | Path,
    *,
    h3_resolution: int = 15,
    key_method: str = 'h3',
) -> DayTypeResult:
    """Extract DayTypes from a GTFS feed directory or zip archive.

    :param gtfs_path: Path to a GTFS directory or zip archive.
    :param h3_resolution: H3 resolution used for Route Pattern keys.
    :param key_method: ``h3`` for H3 keys or ``stop_ids`` for direct stop-id keys.
    :returns: Extracted DayTypes, date mapping, and Route Patterns.
    """

    trips = read_gtfs_table(gtfs_path, 'trips.txt')
    stop_times = read_gtfs_table(gtfs_path, 'stop_times.txt')
    stops = read_gtfs_table(gtfs_path, 'stops.txt')
    calendar_rows = read_gtfs_table(gtfs_path, 'calendar.txt')
    calendar_date_rows = read_gtfs_table(gtfs_path, 'calendar_dates.txt')

    dates_by_service = service_dates(calendar_rows, calendar_date_rows)
    route_patterns_by_trip = build_route_patterns(
        trips,
        stop_times,
        stops,
        h3_resolution=h3_resolution,
        key_method=key_method,
    )
    times_by_trip = _trip_time_bounds(stop_times)

    schedule_by_date: dict[object, set[TripSpec]] = defaultdict(set)
    for trip in trips:
        trip_id = trip['trip_id']
        service_id = trip['service_id']
        if trip_id not in times_by_trip or trip_id not in route_patterns_by_trip:
            continue
        dep, arr = times_by_trip[trip_id]
        pattern = route_patterns_by_trip[trip_id].key
        spec = TripSpec(pattern=pattern, dep=dep, arr=arr, trip_id=trip_id)
        for current_date in dates_by_service.get(service_id, set()):
            schedule_by_date[current_date].add(spec)

    dates_by_schedule: dict[tuple[TripSpec, ...], list[object]] = defaultdict(list)
    for current_date, trips_for_date in schedule_by_date.items():
        dates_by_schedule[tuple(sorted(trips_for_date))].append(current_date)

    daytypes: list[DayType] = []
    date_to_daytype: dict[object, int] = {}
    for idx, (schedule, dates) in enumerate(
        sorted(dates_by_schedule.items(), key=lambda item: min(item[1]))
    ):
        sorted_dates = tuple(sorted(dates))
        daytype = DayType(
            id=idx,
            dates=sorted_dates,
            representative_date=sorted_dates[0],
            trips=frozenset(schedule),
        )
        daytypes.append(daytype)
        for current_date in sorted_dates:
            date_to_daytype[current_date] = idx

    return DayTypeResult(
        daytypes=tuple(daytypes),
        date_to_daytype=date_to_daytype,
        route_patterns={pattern.key: pattern for pattern in route_patterns_by_trip.values()},
    )


def _trip_time_bounds(stop_times: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    """Return first departure and last arrival for each trip.

    :param stop_times: Rows from ``stop_times.txt``.
    :returns: Mapping from ``trip_id`` to ``(departure, arrival)`` in seconds.
    """
    rows_by_trip: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in stop_times:
        rows_by_trip[row['trip_id']].append(row)

    bounds = {}
    for trip_id, rows in rows_by_trip.items():
        ordered = sorted(rows, key=lambda row: int(row.get('stop_sequence', '0')))
        first = ordered[0]
        last = ordered[-1]
        dep = parse_gtfs_time(first.get('departure_time') or first.get('arrival_time'))
        arr = parse_gtfs_time(last.get('arrival_time') or last.get('departure_time'))
        bounds[trip_id] = (dep, arr)
    return bounds
