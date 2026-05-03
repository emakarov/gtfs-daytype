"""Compare DayTypes from a GTFS feed with exact and tolerant distances.

Run from the package root:

.. code-block:: bash

   uv run python examples/compare_daytypes.py examples/data/mdb-3-202402080013.zip --epsilon 0 1 3 5
   uv run python examples/compare_daytypes.py examples/data/mdb-734-202602180121.zip --epsilon 0 1 3 5
"""

import argparse
from statistics import mean

from gtfs_daytype import compare_daytypes, extract_daytypes


def main() -> None:
    """Run the comparison example."""
    parser = argparse.ArgumentParser()
    parser.add_argument('feed', help='Path to a GTFS zip archive or folder.')
    parser.add_argument('--epsilon', type=int, nargs='+', default=[0, 1, 3, 5])
    args = parser.parse_args()

    result = extract_daytypes(args.feed)
    for epsilon in args.epsilon:
        rows = compare_daytypes(result.daytypes, epsilon_minutes=epsilon)
        distances = [row.distance for row in rows]
        if not distances:
            print(f'epsilon={epsilon}: no DayType pairs')
            continue
        print(
            f'epsilon={epsilon}: pairs={len(rows)}, '
            f'min={min(distances):.3f}, mean={mean(distances):.3f}, max={max(distances):.3f}'
        )


if __name__ == '__main__':
    main()
