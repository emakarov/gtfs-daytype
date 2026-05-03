gtfs-daytype
============

Minimal Python package for extracting recurring public transit DayTypes from
standard GTFS feeds and comparing their schedule sets.

The package implements the core methodology from the DayType paper:

* stable Route Pattern keys from ordered stop coordinates using H3 cells;
* date-level DayType extraction from GTFS calendars, trips, and stop times;
* exact schedule-set comparison;
* time-tolerant one-to-one trip matching for small timetable shifts.

Install for Development
-----------------------

.. code-block:: bash

   uv sync --extra dev

Example Data
------------

The repository includes two small GTFS snapshots under Git LFS for examples and
paper-method validation:

* ``examples/data/mdb-3-202402080013.zip``: Barrie Transit.
* ``examples/data/mdb-734-202602180121.zip``: Halifax Transit.

After cloning the repository, make sure Git LFS files are present:

.. code-block:: bash

   git lfs pull

All commands below should be run from the package root:

.. code-block:: bash

   cd packages/gtfs-daytype

Quick CLI Tour
--------------

The package installs a command named ``gtfs-daytype``.

Show help:

.. code-block:: bash

   uv run gtfs-daytype --help

Extract DayTypes from a GTFS feed:

.. code-block:: bash

   uv run gtfs-daytype extract examples/data/mdb-3-202402080013.zip --out results

This writes:

* ``results/daytypes.csv``: one row per DayType;
* ``results/calendar_daytypes.csv``: date-to-DayType assignment;
* ``results/daytype_trips.csv``: Route-Pattern-time trip specifications;
* ``results/route_patterns.csv``: stable Route Pattern keys and stop sequences.

Compare DayTypes with exact and time-tolerant metrics:

.. code-block:: bash

   uv run gtfs-daytype compare examples/data/mdb-3-202402080013.zip --epsilon 0 1 3 5 --out results

This additionally writes ``results/daytype_similarity.csv``.

Command Line Examples
---------------------

Use any GTFS ``.zip`` archive or extracted GTFS folder as input.

Extract DayTypes and write output CSV files:

.. code-block:: bash

   uv run gtfs-daytype extract examples/data/mdb-3-202402080013.zip --out results/barrie

Extract using direct stop-id keys instead of H3 keys. This is useful for
debugging because the key is based on the GTFS stop sequence itself:

.. code-block:: bash

   uv run gtfs-daytype extract examples/data/mdb-3-202402080013.zip \
      --key-method stop_ids \
      --out results/barrie-stop-ids

Compare DayTypes with exact matching only:

.. code-block:: bash

   uv run gtfs-daytype compare examples/data/mdb-3-202402080013.zip --epsilon 0 --out results/barrie

Compare DayTypes with exact plus one-, three-, and five-minute tolerances:

.. code-block:: bash

   uv run gtfs-daytype compare examples/data/mdb-3-202402080013.zip \
      --epsilon 0 1 3 5 \
      --out results/barrie

Print the full date-to-DayType calendar:

.. code-block:: bash

   uv run gtfs-daytype calendar examples/data/mdb-3-202402080013.zip

Print only a date range:

.. code-block:: bash

   uv run gtfs-daytype calendar examples/data/mdb-3-202402080013.zip \
      --start-date 2024-01-01 \
      --end-date 2024-01-31

Print and save the calendar table:

.. code-block:: bash

   uv run gtfs-daytype calendar examples/data/mdb-3-202402080013.zip --out results/calendar.csv

Inspect Route Pattern keys for one route:

.. code-block:: bash

   uv run gtfs-daytype inspect-route examples/data/mdb-3-202402080013.zip --route-id ROUTE_ID

Inspect only selected ``shape_id`` values on a route:

.. code-block:: bash

   uv run gtfs-daytype inspect-route examples/data/mdb-3-202402080013.zip \
      --route-id ROUTE_ID \
      --shape-id SHAPE_ID_1 \
      --shape-id SHAPE_ID_2 \
      --out results/route-inspection.csv

Output Files
------------

``extract`` and ``compare`` write these files:

``daytypes.csv``
   One row per extracted DayType, with representative date, number of dates,
   and number of trip specifications.

``calendar_daytypes.csv``
   Date-to-DayType assignment.

``daytype_trips.csv``
   Trip specifications defining each DayType: Route Pattern key, first
   departure time, last arrival time, and source ``trip_id`` for traceability.

``route_patterns.csv``
   Stable Route Pattern keys, ordered H3 cells, and ordered stop identifiers.

``daytype_similarity.csv``
   Pairwise exact or time-tolerant schedule similarity. Written by
   ``compare``.

Tutorial 1: Reproduce a Paper Case Study
----------------------------------------

Use the included Barrie Transit GTFS snapshot:

Run extraction:

.. code-block:: bash

   uv run gtfs-daytype extract \
      examples/data/mdb-3-202402080013.zip \
      --out results/mdb-3-202402080013

Expected terminal summary:

.. code-block:: text

   DayTypes: 3
   Dates assigned: 84
   DT0: representative_date=2024-01-12, dates=60, trips=658
   DT1: representative_date=2024-01-13, dates=13, trips=571
   DT2: representative_date=2024-01-14, dates=11, trips=307

Tutorial 2: Compare DayTypes
----------------------------

Compute exact and tolerant schedule similarity:

.. code-block:: bash

   uv run gtfs-daytype compare \
      examples/data/mdb-3-202402080013.zip \
      --epsilon 0 1 3 5 \
      --out results/mdb-3-202402080013

Inspect the output:

.. code-block:: bash

   head results/mdb-3-202402080013/daytype_similarity.csv

Columns include:

* ``distance``: normalized exact or tolerant DayType distance;
* ``matches``: exact or time-tolerant one-to-one matches;
* ``containment_a_in_b`` and ``containment_b_in_a``: directional containment;
* ``unmatched_a`` and ``unmatched_b``: unmatched trips after tolerance;
* ``trip_count_imbalance``: absolute difference in schedule-set sizes.

Tutorial 3: Print the Date Calendar
-----------------------------------

Print the date-to-DayType table:

.. code-block:: bash

   uv run gtfs-daytype calendar \
      examples/data/mdb-3-202402080013.zip

Limit to a date range and also save CSV:

.. code-block:: bash

   uv run gtfs-daytype calendar \
      examples/data/mdb-3-202402080013.zip \
      --start-date 2024-01-12 \
      --end-date 2024-01-21 \
      --out results/barrie-calendar-sample.csv

Example output:

.. code-block:: text

   date        dow  daytype  representative  trips  dates
   ----------  ---  -------  --------------  -----  -----
   2024-01-12  Fri  DT0      2024-01-12        658     60
   2024-01-13  Sat  DT1      2024-01-13        571     13
   2024-01-14  Sun  DT2      2024-01-14        307     11

Tutorial 4: Inspect Shape-ID Inconsistency
------------------------------------------

Barrie Route 2A in the paper uses two different ``shape_id`` values for the
same passenger-facing stop sequence. The H3 Route Pattern key should collapse
them to one key.

.. code-block:: bash

   uv run gtfs-daytype inspect-route \
      examples/data/mdb-3-202402080013.zip \
      --route-id c8bb5d6b-0a67-426c-8742-36d10b8c15b8 \
      --shape-id 58ea5474-ef60-4dbc-bd74-5c122b012d32 \
      --shape-id c0134c50-192b-4a6c-8d93-d0534d3b0fab \
      --out results/barrie-route-2a-inspection.csv

Expected terminal summary:

.. code-block:: text

   Matched trips: 71
   Trips by shape_id:
     58ea5474-ef60-4dbc-bd74-5c122b012d32: 58
     c0134c50-192b-4a6c-8d93-d0534d3b0fab: 13
   Route Pattern keys: 1

Tutorial 5: Validate Paper Feeds
--------------------------------

Run validation against the example GTFS snapshots:

.. code-block:: bash

   uv run python scripts/validate_paper_feeds.py

Expected output:

.. code-block:: text

   mdb-3-202402080013.zip: DayType counts match paper values
   mdb-734-202602180121.zip: DayType counts match paper values
   Barrie Route 2A: two shape_id values collapse to one H3 Route Pattern key

Python
------

.. code-block:: python

   from gtfs_daytype import compare_daytypes, extract_daytypes

   result = extract_daytypes('feed.zip')
   distances = compare_daytypes(result.daytypes, epsilon_minutes=1)

Python Examples
---------------

Basic extraction:

.. code-block:: python

   from gtfs_daytype import extract_daytypes

   result = extract_daytypes('feed.zip')

   for daytype in result.daytypes:
       print(daytype.id, daytype.representative_date, len(daytype.dates), len(daytype.trips))

Print date-to-DayType assignments:

.. code-block:: python

   from gtfs_daytype import extract_daytypes

   result = extract_daytypes('feed.zip')

   for current_date, daytype_id in sorted(result.date_to_daytype.items()):
       print(current_date, daytype_id)

Compare all DayTypes at a one-minute tolerance:

.. code-block:: python

   from gtfs_daytype import compare_daytypes, extract_daytypes

   result = extract_daytypes('feed.zip')
   rows = compare_daytypes(result.daytypes, epsilon_minutes=1)

   for row in rows:
       print(row.daytype_a, row.daytype_b, row.distance, row.matches)

Use stop-id keys instead of H3 keys for debugging:

.. code-block:: python

   from gtfs_daytype import extract_daytypes

   result = extract_daytypes('feed.zip', key_method='stop_ids')

Inspect Route Pattern keys from Python:

.. code-block:: python

   from collections import defaultdict

   from gtfs_daytype.io import read_gtfs_table
   from gtfs_daytype.patterns import build_route_patterns

   feed = 'feed.zip'
   trips = read_gtfs_table(feed, 'trips.txt')
   stop_times = read_gtfs_table(feed, 'stop_times.txt')
   stops = read_gtfs_table(feed, 'stops.txt')
   patterns = build_route_patterns(trips, stop_times, stops)

   by_pattern = defaultdict(list)
   for trip in trips:
       if trip['route_id'] == 'ROUTE_ID':
           by_pattern[patterns[trip['trip_id']].key].append(trip['trip_id'])

   for pattern, trip_ids in by_pattern.items():
       print(pattern, len(trip_ids))

Runnable example scripts are provided in ``examples/``:

.. code-block:: bash

   uv run python examples/extract_daytypes.py examples/data/mdb-3-202402080013.zip
   uv run python examples/compare_daytypes.py examples/data/mdb-3-202402080013.zip --epsilon 0 1 3 5
   uv run python examples/calendar_table.py examples/data/mdb-3-202402080013.zip
   uv run python examples/inspect_route_patterns.py examples/data/mdb-3-202402080013.zip --route-id ROUTE_ID

Citation
--------

If you use ``gtfs-daytype`` in academic work, please cite the software package.
The repository includes ``CITATION.cff`` so GitHub and citation managers can
generate citation metadata automatically.

Suggested BibTeX entry:

.. code-block:: bibtex

   @software{makarov_gtfs_daytype_2026,
     author = {Makarov, Evgeny},
     title = {gtfs-daytype: GTFS-Based Transit DayType Extraction and Schedule Similarity},
     year = {2026},
     version = {0.1.0},
     url = {https://github.com/emakarov/gtfs-daytype}
   }

When citing the methodology rather than only the implementation, cite both this
software package and the associated paper once the paper citation is available.

Credits
-------

The initial idea for using DayTypes as recurring public-transit schedule
classes was contributed by Georgy Taubkin.
