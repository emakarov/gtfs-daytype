"""Resolve GTFS service calendars into active dates."""

from collections import defaultdict
from datetime import date, timedelta

from gtfs_daytype.time import parse_gtfs_date


WEEKDAY_COLUMNS = (
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
)


def service_dates(
    calendar_rows: list[dict[str, str]],
    calendar_date_rows: list[dict[str, str]],
) -> dict[str, set[date]]:
    """Return active service dates for each GTFS ``service_id``.

    :param calendar_rows: Rows from ``calendar.txt``.
    :param calendar_date_rows: Rows from ``calendar_dates.txt``.
    :returns: Mapping from ``service_id`` to active dates.
    """

    dates_by_service: dict[str, set[date]] = defaultdict(set)

    for row in calendar_rows:
        service_id = row['service_id']
        start = parse_gtfs_date(row['start_date'])
        end = parse_gtfs_date(row['end_date'])
        current = start
        while current <= end:
            if str(row.get(WEEKDAY_COLUMNS[current.weekday()], '0')).strip() == '1':
                dates_by_service[service_id].add(current)
            current += timedelta(days=1)

    for row in calendar_date_rows:
        service_id = row['service_id']
        current = parse_gtfs_date(row['date'])
        exception_type = int(row.get('exception_type', '1'))
        if exception_type == 1:
            dates_by_service[service_id].add(current)
        elif exception_type == 2:
            dates_by_service[service_id].discard(current)

    return dict(dates_by_service)
