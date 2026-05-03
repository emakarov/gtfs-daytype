"""Extract DayTypes from a GTFS feed and print a compact summary.

Run from the package root:

.. code-block:: bash

   uv run python examples/extract_daytypes.py examples/data/mdb-3-202402080013.zip
   uv run python examples/extract_daytypes.py examples/data/mdb-734-202602180121.zip
"""

import argparse

from gtfs_daytype import extract_daytypes


def main() -> None:
    """Run the extraction example."""
    parser = argparse.ArgumentParser()
    parser.add_argument('feed', help='Path to a GTFS zip archive or folder.')
    args = parser.parse_args()

    result = extract_daytypes(args.feed)
    print(f'DayTypes: {len(result.daytypes)}')
    print(f'Dates assigned: {len(result.date_to_daytype)}')
    print(f'Route Patterns: {len(result.route_patterns)}')
    for daytype in result.daytypes:
        print(
            f'DT{daytype.id}: representative_date={daytype.representative_date.isoformat()}, '
            f'dates={len(daytype.dates)}, trips={len(daytype.trips)}'
        )


if __name__ == '__main__':
    main()
