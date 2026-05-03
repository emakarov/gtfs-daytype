"""Parse and format GTFS date and time values."""


def parse_gtfs_date(value: str):
    """Parse a GTFS ``YYYYMMDD`` date value.

    :param value: GTFS date string.
    :returns: Python ``date`` object.
    """
    from datetime import date

    value = str(value).strip()
    return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))


def parse_gtfs_time(value: str) -> int:
    """Parse a GTFS ``HH:MM:SS`` time value.

    GTFS allows hours greater than 23 for after-midnight service.

    :param value: GTFS time string.
    :returns: Seconds after service-day midnight.
    :raises ValueError: If the value is not a three-part GTFS time.
    """

    parts = str(value).strip().split(':')
    if len(parts) != 3:
        raise ValueError(f'Invalid GTFS time: {value!r}')
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])


def format_gtfs_time(seconds: int) -> str:
    """Format seconds after service-day midnight as GTFS time.

    :param seconds: Seconds after service-day midnight.
    :returns: GTFS ``HH:MM:SS`` time string.
    """
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}'
