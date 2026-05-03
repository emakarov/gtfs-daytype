"""Validate package outputs against the paper's GTFS case-study feeds."""

import argparse
from collections import Counter, defaultdict
from pathlib import Path

from gtfs_daytype import extract_daytypes
from gtfs_daytype.io import read_gtfs_table
from gtfs_daytype.patterns import build_route_patterns


EXPECTED_DAYTYPES = {
    'mdb-3-202402080013': [
        ('2024-01-12', 60, 658),
        ('2024-01-13', 13, 571),
        ('2024-01-14', 11, 307),
    ],
    'mdb-734-202602180121': [
        ('2026-02-23', 59, 4200),
        ('2026-02-28', 12, 2765),
        ('2026-03-01', 11, 2217),
        ('2026-04-03', 1, 2147),
        ('2026-04-05', 1, 2213),
    ],
}

BARRIE_ROUTE_2A = 'c8bb5d6b-0a67-426c-8742-36d10b8c15b8'
BARRIE_ROUTE_2A_SHAPES = {
    '58ea5474-ef60-4dbc-bd74-5c122b012d32',
    'c0134c50-192b-4a6c-8d93-d0534d3b0fab',
}


def main() -> None:
    """Run paper-feed validation checks."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data-dir',
        default='examples/data',
        help='Directory containing paper GTFS zip snapshots.',
    )
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    for feed_id, expected in EXPECTED_DAYTYPES.items():
        feed_path = data_dir / f'{feed_id}.zip'
        _validate_daytypes(feed_path, expected)

    _validate_barrie_shape_id_collapse(data_dir / 'mdb-3-202402080013.zip')


def _validate_daytypes(feed_path: Path, expected: list[tuple[str, int, int]]) -> None:
    """Validate DayType counts against expected paper values.

    :param feed_path: Path to a GTFS zip archive.
    :param expected: Expected ``(representative_date, num_dates, num_trips)`` rows.
    """
    result = extract_daytypes(feed_path)
    actual = [
        (
            daytype.representative_date.isoformat(),
            len(daytype.dates),
            len(daytype.trips),
        )
        for daytype in result.daytypes
    ]
    if actual != expected:
        raise AssertionError(f'{feed_path.name}: expected {expected}, got {actual}')
    print(f'{feed_path.name}: DayType counts match paper values')


def _validate_barrie_shape_id_collapse(feed_path: Path) -> None:
    """Validate that Barrie's Route 2A shape variants collapse to one H3 key.

    :param feed_path: Path to the Barrie GTFS zip archive.
    """
    trips = read_gtfs_table(feed_path, 'trips.txt')
    stops = read_gtfs_table(feed_path, 'stops.txt')
    stop_times = read_gtfs_table(feed_path, 'stop_times.txt')
    patterns = build_route_patterns(trips, stop_times, stops)

    route_trips = [
        trip
        for trip in trips
        if trip.get('route_id') == BARRIE_ROUTE_2A
        and trip.get('shape_id') in BARRIE_ROUTE_2A_SHAPES
    ]
    by_shape = Counter(trip['shape_id'] for trip in route_trips)
    by_key = defaultdict(set)
    for trip in route_trips:
        by_key[patterns[trip['trip_id']].key].add(trip['shape_id'])

    expected_shape_counts = {
        '58ea5474-ef60-4dbc-bd74-5c122b012d32': 58,
        'c0134c50-192b-4a6c-8d93-d0534d3b0fab': 13,
    }
    if dict(by_shape) != expected_shape_counts:
        raise AssertionError(f'Unexpected Route 2A shape counts: {dict(by_shape)}')
    if len(by_key) != 1:
        raise AssertionError(f'Expected one H3 Route Pattern key, got {len(by_key)}')

    pattern = patterns[route_trips[0]['trip_id']]
    if len(pattern.stop_ids) != 29:
        raise AssertionError(f'Expected 29 stops, got {len(pattern.stop_ids)}')

    print('Barrie Route 2A: two shape_id values collapse to one H3 Route Pattern key')


if __name__ == '__main__':
    main()
