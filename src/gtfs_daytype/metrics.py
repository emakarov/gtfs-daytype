"""Compare DayTypes using exact and time-tolerant schedule-set metrics."""

from collections import defaultdict, deque
from itertools import combinations

from gtfs_daytype.models import DayType, SimilarityResult, TripSpec


def compare_daytypes(
    daytypes: tuple[DayType, ...] | list[DayType],
    *,
    epsilon_minutes: int = 0,
) -> list[SimilarityResult]:
    """Compute pairwise exact or time-tolerant DayType distances.

    :param daytypes: DayTypes to compare.
    :param epsilon_minutes: Time tolerance for matching departure and arrival times.
    :returns: Pairwise comparison rows.
    """

    epsilon_seconds = epsilon_minutes * 60
    rows = []
    for a, b in combinations(daytypes, 2):
        matches = tolerant_match_count(a.trips, b.trips, epsilon_seconds)
        size_a = len(a.trips)
        size_b = len(b.trips)
        rows.append(
            SimilarityResult(
                daytype_a=a.id,
                daytype_b=b.id,
                epsilon_minutes=epsilon_minutes,
                matches=matches,
                size_a=size_a,
                size_b=size_b,
                distance=normalized_distance(matches, size_a, size_b),
                containment_a_in_b=matches / size_a if size_a else 0.0,
                containment_b_in_a=matches / size_b if size_b else 0.0,
                unmatched_a=size_a - matches,
                unmatched_b=size_b - matches,
                trip_count_imbalance=abs(size_a - size_b),
            )
        )
    return rows


def exact_match_count(a: frozenset[TripSpec], b: frozenset[TripSpec]) -> int:
    """Count exact shared trip specifications.

    :param a: First trip-specification set.
    :param b: Second trip-specification set.
    :returns: Number of exact shared specifications.
    """
    return len(a & b)


def tolerant_match_count(
    a: frozenset[TripSpec],
    b: frozenset[TripSpec],
    epsilon_seconds: int,
) -> int:
    """Count maximum one-to-one tolerant trip matches.

    :param a: First trip-specification set.
    :param b: Second trip-specification set.
    :param epsilon_seconds: Maximum allowed departure and arrival difference.
    :returns: Maximum number of unique matches.
    """
    if epsilon_seconds == 0:
        return exact_match_count(a, b)

    total = 0
    by_pattern_a: dict[str, list[TripSpec]] = defaultdict(list)
    by_pattern_b: dict[str, list[TripSpec]] = defaultdict(list)
    for spec in a:
        by_pattern_a[spec.pattern].append(spec)
    for spec in b:
        by_pattern_b[spec.pattern].append(spec)

    for pattern, left in by_pattern_a.items():
        right = by_pattern_b.get(pattern)
        if right:
            total += _hopcroft_karp(left, right, epsilon_seconds)
    return total


def normalized_distance(matches: int, size_a: int, size_b: int) -> float:
    """Compute normalized symmetric-difference distance from a match count.

    :param matches: Number of matched trip specifications.
    :param size_a: Size of the first DayType schedule set.
    :param size_b: Size of the second DayType schedule set.
    :returns: Normalized distance in ``[0, 1]``.
    """
    union_size = size_a + size_b - matches
    if union_size == 0:
        return 0.0
    return (size_a + size_b - 2 * matches) / union_size


def _hopcroft_karp(
    left: list[TripSpec],
    right: list[TripSpec],
    epsilon_seconds: int,
) -> int:
    """Solve cardinality matching for one Route Pattern.

    :param left: Trip specifications from the first DayType.
    :param right: Trip specifications from the second DayType.
    :param epsilon_seconds: Maximum allowed departure and arrival difference.
    :returns: Maximum bipartite matching cardinality.
    """
    adjacency = [
        [
            j
            for j, y in enumerate(right)
            if abs(x.dep - y.dep) <= epsilon_seconds
            and abs(x.arr - y.arr) <= epsilon_seconds
        ]
        for x in left
    ]

    pair_u = [-1] * len(left)
    pair_v = [-1] * len(right)
    dist = [0] * len(left)

    def bfs() -> bool:
        queue: deque[int] = deque()
        found = False
        for u in range(len(left)):
            if pair_u[u] == -1:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = -1
        while queue:
            u = queue.popleft()
            for v in adjacency[u]:
                matched_u = pair_v[v]
                if matched_u == -1:
                    found = True
                elif dist[matched_u] == -1:
                    dist[matched_u] = dist[u] + 1
                    queue.append(matched_u)
        return found

    def dfs(u: int) -> bool:
        for v in adjacency[u]:
            matched_u = pair_v[v]
            if matched_u == -1 or (
                dist[matched_u] == dist[u] + 1 and dfs(matched_u)
            ):
                pair_u[u] = v
                pair_v[v] = u
                return True
        dist[u] = -1
        return False

    matching = 0
    while bfs():
        for u in range(len(left)):
            if pair_u[u] == -1 and dfs(u):
                matching += 1
    return matching
