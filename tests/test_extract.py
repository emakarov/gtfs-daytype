"""Test GTFS DayType extraction."""

from gtfs_daytype import extract_daytypes


def test_extract_daytypes_from_minimal_gtfs_folder(tmp_path):
    """Check DayType extraction on a minimal synthetic GTFS folder."""
    _write(
        tmp_path / 'stops.txt',
        """stop_id,stop_name,stop_lat,stop_lon
s1,First,43.0,-79.0
s2,Second,43.1,-79.1
""",
    )
    _write(
        tmp_path / 'trips.txt',
        """route_id,service_id,trip_id
r,weekday,t_weekday
r,saturday,t_saturday
""",
    )
    _write(
        tmp_path / 'stop_times.txt',
        """trip_id,arrival_time,departure_time,stop_id,stop_sequence
t_weekday,08:00:00,08:00:00,s1,1
t_weekday,08:30:00,08:30:00,s2,2
t_saturday,09:00:00,09:00:00,s1,1
t_saturday,09:30:00,09:30:00,s2,2
""",
    )
    _write(
        tmp_path / 'calendar.txt',
        """service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
weekday,1,1,1,1,1,0,0,20260105,20260111
saturday,0,0,0,0,0,1,0,20260105,20260111
""",
    )

    result = extract_daytypes(tmp_path, key_method='stop_ids')

    assert len(result.daytypes) == 2
    assert [len(daytype.dates) for daytype in result.daytypes] == [5, 1]
    assert [len(daytype.trips) for daytype in result.daytypes] == [1, 1]


def _write(path, text):
    """Write UTF-8 text to a test file.

    :param path: Destination path.
    :param text: Text content.
    """
    path.write_text(text, encoding='utf-8')
