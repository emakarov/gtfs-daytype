"""Define public data models for GTFS DayType extraction."""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, order=True)
class TripSpec:
    """Represent a timetable atom used to define DayTypes.

    :ivar pattern: Stable Route Pattern key for the trip.
    :ivar dep: First departure time in seconds after service-day midnight.
    :ivar arr: Last arrival time in seconds after service-day midnight.
    :ivar trip_id: Source GTFS ``trip_id`` retained for traceability only. It is
        excluded from equality and hashing because DayType identity is based on
        ``(pattern, dep, arr)``.
    """

    pattern: str
    dep: int
    arr: int
    trip_id: str = field(default='', compare=False, hash=False)


@dataclass(frozen=True)
class RoutePattern:
    """Represent a stable ordered stop sequence.

    :ivar key: Deterministic Route Pattern key derived from ``cells``.
    :ivar stop_ids: Ordered GTFS stop identifiers visited by the pattern.
    :ivar cells: Ordered key sequence used to identify the pattern. With the
        default H3 method, these are H3 cells; with ``stop_ids`` they are the
        ordered stop identifiers.
    """

    key: str
    stop_ids: tuple[str, ...]
    cells: tuple[str, ...]


@dataclass(frozen=True)
class DayType:
    """Represent dates sharing the same Route-Pattern-time schedule.

    :ivar id: Integer DayType identifier assigned within one extraction result.
    :ivar dates: Calendar dates assigned to this DayType.
    :ivar representative_date: First calendar date assigned to this DayType.
    :ivar trips: Set of trip specifications defining the DayType.
    """

    id: int
    dates: tuple[date, ...]
    representative_date: date
    trips: frozenset[TripSpec]


@dataclass(frozen=True)
class DayTypeResult:
    """Represent the output of a GTFS DayType extraction run.

    :ivar daytypes: Extracted DayTypes sorted by representative date.
    :ivar date_to_daytype: Mapping from calendar date to DayType identifier.
    :ivar route_patterns: Mapping from Route Pattern key to Route Pattern.
    """

    daytypes: tuple[DayType, ...]
    date_to_daytype: dict[date, int]
    route_patterns: dict[str, RoutePattern]


@dataclass(frozen=True)
class SimilarityResult:
    """Represent a pairwise DayType comparison result.

    :ivar daytype_a: Identifier of the first compared DayType.
    :ivar daytype_b: Identifier of the second compared DayType.
    :ivar epsilon_minutes: Time tolerance used for matching, in minutes.
    :ivar matches: Number of exact or time-tolerant one-to-one trip matches.
    :ivar size_a: Number of trip specifications in the first DayType.
    :ivar size_b: Number of trip specifications in the second DayType.
    :ivar distance: Normalized exact or time-tolerant schedule-set distance.
    :ivar containment_a_in_b: Share of first-DayType trips matched in the
        second DayType.
    :ivar containment_b_in_a: Share of second-DayType trips matched in the
        first DayType.
    :ivar unmatched_a: Number of first-DayType trips unmatched after tolerance.
    :ivar unmatched_b: Number of second-DayType trips unmatched after tolerance.
    :ivar trip_count_imbalance: Absolute difference between ``size_a`` and
        ``size_b``.
    """

    daytype_a: int
    daytype_b: int
    epsilon_minutes: int
    matches: int
    size_a: int
    size_b: int
    distance: float
    containment_a_in_b: float
    containment_b_in_a: float
    unmatched_a: int
    unmatched_b: int
    trip_count_imbalance: int
