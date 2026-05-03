"""Read GTFS source tables from directories or zip archives."""

import csv
import zipfile
from pathlib import Path


def read_gtfs_table(gtfs_path: str | Path, name: str) -> list[dict[str, str]]:
    """Read a GTFS text table from a feed directory or zip archive.

    :param gtfs_path: Path to a GTFS directory or ``.zip`` archive.
    :param name: GTFS table filename, for example ``trips.txt``.
    :returns: Table rows as dictionaries keyed by GTFS column name.
    :raises FileNotFoundError: If ``gtfs_path`` does not exist.
    """

    path = Path(gtfs_path)
    if path.is_dir():
        table_path = path / name
        if not table_path.exists():
            return []
        with table_path.open(newline='', encoding='utf-8-sig') as handle:
            return list(csv.DictReader(handle))

    if path.is_file():
        with zipfile.ZipFile(path) as archive:
            try:
                with archive.open(name) as handle:
                    text = (line.decode('utf-8-sig') for line in handle)
                    return list(csv.DictReader(text))
            except KeyError:
                return []

    raise FileNotFoundError(f'GTFS path does not exist: {path}')
