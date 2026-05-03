Paper Validation Data
=====================

The package includes two small GTFS snapshots under Git LFS for reproducing
paper validation checks.

Included feed snapshots:

* ``examples/data/mdb-3-202402080013.zip``: Barrie Transit, Mobility
  Database.
* ``examples/data/mdb-734-202602180121.zip``: Halifax Transit, Mobility
  Database.

After cloning the repository, make sure Git LFS files are present:

.. code-block:: bash

   git lfs pull

Then run:

.. code-block:: bash

   uv run python scripts/validate_paper_feeds.py
