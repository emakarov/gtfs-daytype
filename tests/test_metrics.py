"""Test DayType similarity metrics."""

from gtfs_daytype.metrics import compare_daytypes
from gtfs_daytype.models import DayType, TripSpec


def test_tolerant_distance_matches_shifted_trip():
    """Check that one-minute shifts match under one-minute tolerance."""
    a = DayType(0, tuple(), None, frozenset({TripSpec('p', 8 * 3600, 9 * 3600)}))
    b = DayType(1, tuple(), None, frozenset({TripSpec('p', 8 * 3600 + 60, 9 * 3600 + 60)}))

    exact = compare_daytypes([a, b], epsilon_minutes=0)[0]
    tolerant = compare_daytypes([a, b], epsilon_minutes=1)[0]

    assert exact.matches == 0
    assert exact.distance == 1.0
    assert tolerant.matches == 1
    assert tolerant.distance == 0.0


def test_trip_id_is_traceability_not_identity():
    """Check that trip identifiers do not define schedule-set identity."""
    assert TripSpec('p', 8 * 3600, 9 * 3600, 'weekday_trip') == TripSpec(
        'p',
        8 * 3600,
        9 * 3600,
        'saturday_trip',
    )
