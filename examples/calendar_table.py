"""Print a date-to-DayType table from a GTFS feed.

Run from the package root:

.. code-block:: bash

   uv run python examples/calendar_table.py examples/data/mdb-3-202402080013.zip
   uv run python examples/calendar_table.py examples/data/mdb-734-202602180121.zip
"""

import argparse

from gtfs_daytype import extract_daytypes


def main() -> None:
    """Run the calendar-table example."""
    parser = argparse.ArgumentParser()
    parser.add_argument('feed', help='Path to a GTFS zip archive or folder.')
    args = parser.parse_args()

    result = extract_daytypes(args.feed)
    daytypes = {daytype.id: daytype for daytype in result.daytypes}
    print('date        dow  daytype  representative  trips')
    print('----------  ---  -------  --------------  -----')
    for current_date, daytype_id in sorted(result.date_to_daytype.items()):
        daytype = daytypes[daytype_id]
        print(
            f'{current_date.isoformat()}  {current_date:%a}  '
            f'DT{daytype_id:<5}  {daytype.representative_date.isoformat()}  '
            f'{len(daytype.trips):>5}'
        )


if __name__ == '__main__':
    main()
