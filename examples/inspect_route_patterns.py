"""Inspect Route Pattern keys for trips on one GTFS route.

Run from the package root:

.. code-block:: bash

   uv run python examples/inspect_route_patterns.py examples/data/mdb-3-202402080013.zip \
      --route-id c8bb5d6b-0a67-426c-8742-36d10b8c15b8 \
      --shape-id 58ea5474-ef60-4dbc-bd74-5c122b012d32 \
      --shape-id c0134c50-192b-4a6c-8d93-d0534d3b0fab
"""

import argparse
from collections import defaultdict

from gtfs_daytype.io import read_gtfs_table
from gtfs_daytype.patterns import build_route_patterns


def main() -> None:
    """Run the Route Pattern inspection example."""
    parser = argparse.ArgumentParser()
    parser.add_argument('feed', help='Path to a GTFS zip archive or folder.')
    parser.add_argument('--route-id', required=True)
    parser.add_argument('--shape-id', action='append', default=[])
    args = parser.parse_args()

    trips = read_gtfs_table(args.feed, 'trips.txt')
    stop_times = read_gtfs_table(args.feed, 'stop_times.txt')
    stops = read_gtfs_table(args.feed, 'stops.txt')
    patterns = build_route_patterns(trips, stop_times, stops)
    shape_filter = set(args.shape_id)

    by_pattern = defaultdict(list)
    for trip in trips:
        if trip.get('route_id') != args.route_id:
            continue
        if shape_filter and trip.get('shape_id') not in shape_filter:
            continue
        pattern = patterns[trip['trip_id']]
        by_pattern[pattern.key].append(trip)

    for pattern_key, pattern_trips in sorted(by_pattern.items()):
        shape_ids = sorted({trip.get('shape_id', '') for trip in pattern_trips})
        print(f'{pattern_key}: trips={len(pattern_trips)}, shape_ids={", ".join(shape_ids)}')


if __name__ == '__main__':
    main()
