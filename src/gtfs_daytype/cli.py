"""Command line interface for GTFS DayType extraction and comparison."""

import argparse
import csv
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from gtfs_daytype.extract import extract_daytypes
from gtfs_daytype.io import read_gtfs_table
from gtfs_daytype.metrics import compare_daytypes
from gtfs_daytype.patterns import build_route_patterns
from gtfs_daytype.time import format_gtfs_time, parse_gtfs_date


def main() -> None:
    """Run the ``gtfs-daytype`` command line interface."""
    parser = argparse.ArgumentParser(
        prog='gtfs-daytype',
        description='Extract recurring DayTypes and compare GTFS schedules.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    extract_parser = subparsers.add_parser(
        'extract',
        help='Extract DayTypes from a GTFS feed.',
    )
    extract_parser.add_argument('feed')
    extract_parser.add_argument('--out', required=True)
    extract_parser.add_argument('--h3-resolution', type=int, default=15)
    extract_parser.add_argument('--key-method', choices=['h3', 'stop_ids'], default='h3')
    extract_parser.add_argument('--quiet', action='store_true')

    compare_parser = subparsers.add_parser(
        'compare',
        help='Extract DayTypes and compute pairwise schedule similarity.',
    )
    compare_parser.add_argument('feed')
    compare_parser.add_argument('--out', required=True)
    compare_parser.add_argument('--epsilon', type=int, nargs='+', default=[0, 1, 3, 5])
    compare_parser.add_argument('--h3-resolution', type=int, default=15)
    compare_parser.add_argument('--key-method', choices=['h3', 'stop_ids'], default='h3')
    compare_parser.add_argument('--quiet', action='store_true')

    calendar_parser = subparsers.add_parser(
        'calendar',
        help='Print the date-to-DayType calendar table.',
    )
    calendar_parser.add_argument('feed')
    calendar_parser.add_argument('--out')
    calendar_parser.add_argument('--start-date')
    calendar_parser.add_argument('--end-date')
    calendar_parser.add_argument('--h3-resolution', type=int, default=15)
    calendar_parser.add_argument('--key-method', choices=['h3', 'stop_ids'], default='h3')

    inspect_parser = subparsers.add_parser(
        'inspect-route',
        help='Inspect Route Pattern keys for one GTFS route.',
    )
    inspect_parser.add_argument('feed')
    inspect_parser.add_argument('--route-id', required=True)
    inspect_parser.add_argument('--shape-id', action='append', default=[])
    inspect_parser.add_argument('--out')
    inspect_parser.add_argument('--h3-resolution', type=int, default=15)
    inspect_parser.add_argument('--key-method', choices=['h3', 'stop_ids'], default='h3')

    args = parser.parse_args()
    if args.command == 'extract':
        result = extract_daytypes(
            args.feed,
            h3_resolution=args.h3_resolution,
            key_method=args.key_method,
        )
        _write_extraction(result, Path(args.out))
        if not args.quiet:
            _print_extraction_summary(result, Path(args.out))
    elif args.command == 'compare':
        result = extract_daytypes(
            args.feed,
            h3_resolution=args.h3_resolution,
            key_method=args.key_method,
        )
        _write_extraction(result, Path(args.out))
        rows = _write_comparisons(result, Path(args.out), args.epsilon)
        if not args.quiet:
            _print_extraction_summary(result, Path(args.out))
            _print_comparison_summary(rows)
    elif args.command == 'calendar':
        result = extract_daytypes(
            args.feed,
            h3_resolution=args.h3_resolution,
            key_method=args.key_method,
        )
        rows = _calendar_rows(
            result,
            start_date=args.start_date,
            end_date=args.end_date,
        )
        _print_calendar(rows)
        if args.out:
            _write_calendar(rows, Path(args.out))
    elif args.command == 'inspect-route':
        rows = _inspect_route_patterns(
            args.feed,
            route_id=args.route_id,
            shape_ids=args.shape_id,
            h3_resolution=args.h3_resolution,
            key_method=args.key_method,
        )
        if args.out:
            _write_inspection(rows, Path(args.out))
        _print_inspection_summary(rows)


def _write_extraction(result, out_dir: Path) -> None:
    """Write DayType extraction CSV files.

    :param result: Extraction result.
    :param out_dir: Output directory.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / 'daytypes.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['daytype', 'representative_date', 'num_dates', 'num_trips'],
        )
        writer.writeheader()
        for daytype in result.daytypes:
            writer.writerow(
                {
                    'daytype': daytype.id,
                    'representative_date': daytype.representative_date.isoformat(),
                    'num_dates': len(daytype.dates),
                    'num_trips': len(daytype.trips),
                }
            )

    with (out_dir / 'calendar_daytypes.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['date', 'daytype'])
        writer.writeheader()
        for current_date, daytype_id in sorted(result.date_to_daytype.items()):
            writer.writerow({'date': current_date.isoformat(), 'daytype': daytype_id})

    with (out_dir / 'daytype_trips.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['daytype', 'pattern', 'departure_time', 'arrival_time', 'trip_id'],
        )
        writer.writeheader()
        for daytype in result.daytypes:
            for spec in sorted(daytype.trips):
                writer.writerow(
                    {
                        'daytype': daytype.id,
                        'pattern': spec.pattern,
                        'departure_time': format_gtfs_time(spec.dep),
                        'arrival_time': format_gtfs_time(spec.arr),
                        'trip_id': spec.trip_id,
                    }
                )

    with (out_dir / 'route_patterns.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=['pattern', 'num_stops', 'cells', 'stop_ids'],
        )
        writer.writeheader()
        for key, pattern in sorted(result.route_patterns.items()):
            writer.writerow(
                {
                    'pattern': key,
                    'num_stops': len(pattern.stop_ids),
                    'cells': '|'.join(pattern.cells),
                    'stop_ids': '|'.join(pattern.stop_ids),
                }
            )


def _write_comparisons(result, out_dir: Path, tolerances: list[int]) -> list[dict[str, object]]:
    """Write pairwise DayType comparison CSV files.

    :param result: Extraction result.
    :param out_dir: Output directory.
    :param tolerances: Tolerances in minutes.
    :returns: Written comparison rows.
    """
    rows = []
    with (out_dir / 'daytype_similarity.csv').open('w', newline='') as handle:
        fieldnames = [
            'daytype_a',
            'daytype_b',
            'epsilon_minutes',
            'matches',
            'size_a',
            'size_b',
            'distance',
            'containment_a_in_b',
            'containment_b_in_a',
            'unmatched_a',
            'unmatched_b',
            'trip_count_imbalance',
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for epsilon in tolerances:
            for row in compare_daytypes(result.daytypes, epsilon_minutes=epsilon):
                row_dict = asdict(row)
                rows.append(row_dict)
                writer.writerow(row_dict)
    return rows


def _print_extraction_summary(result, out_dir: Path) -> None:
    """Print a compact extraction summary.

    :param result: Extraction result.
    :param out_dir: Output directory.
    """
    print(f'Output directory: {out_dir}')
    print(f'DayTypes: {len(result.daytypes)}')
    print(f'Dates assigned: {len(result.date_to_daytype)}')
    print(f'Route Patterns: {len(result.route_patterns)}')
    print('DayType summary:')
    for daytype in result.daytypes:
        print(
            f'  DT{daytype.id}: representative_date={daytype.representative_date.isoformat()}, '
            f'dates={len(daytype.dates)}, trips={len(daytype.trips)}'
        )


def _print_comparison_summary(rows: list[dict[str, object]]) -> None:
    """Print a compact pairwise comparison summary.

    :param rows: Pairwise comparison rows.
    """
    if not rows:
        print('Pairwise comparisons: none')
        return

    tolerances = sorted({int(row['epsilon_minutes']) for row in rows})
    print('Pairwise comparison summary:')
    for epsilon in tolerances:
        subset = [row for row in rows if int(row['epsilon_minutes']) == epsilon]
        distances = [float(row['distance']) for row in subset]
        print(
            f'  epsilon={epsilon} min: pairs={len(subset)}, '
            f'min={min(distances):.3f}, mean={mean(distances):.3f}, max={max(distances):.3f}'
        )


def _calendar_rows(result, *, start_date: str | None, end_date: str | None) -> list[dict[str, object]]:
    """Build date-to-DayType calendar rows.

    :param result: Extraction result.
    :param start_date: Optional inclusive ``YYYYMMDD`` or ``YYYY-MM-DD`` start date.
    :param end_date: Optional inclusive ``YYYYMMDD`` or ``YYYY-MM-DD`` end date.
    :returns: Calendar rows sorted by date.
    """
    daytypes = {daytype.id: daytype for daytype in result.daytypes}
    start = _parse_cli_date(start_date) if start_date else None
    end = _parse_cli_date(end_date) if end_date else None

    rows = []
    for current_date, daytype_id in sorted(result.date_to_daytype.items()):
        if start and current_date < start:
            continue
        if end and current_date > end:
            continue
        daytype = daytypes[daytype_id]
        rows.append(
            {
                'date': current_date.isoformat(),
                'weekday': current_date.strftime('%a'),
                'daytype': daytype_id,
                'representative_date': daytype.representative_date.isoformat(),
                'num_trips': len(daytype.trips),
                'num_dates': len(daytype.dates),
            }
        )
    return rows


def _parse_cli_date(value: str):
    """Parse a command-line date value.

    :param value: Date in ``YYYYMMDD`` or ``YYYY-MM-DD`` format.
    :returns: Parsed date.
    """
    return parse_gtfs_date(value.replace('-', ''))


def _print_calendar(rows: list[dict[str, object]]) -> None:
    """Print date-to-DayType calendar rows.

    :param rows: Calendar rows.
    """
    if not rows:
        print('No dates matched the requested range.')
        return

    print('date        dow  daytype  representative  trips  dates')
    print('----------  ---  -------  --------------  -----  -----')
    for row in rows:
        print(
            f'{row["date"]}  {row["weekday"]:>3}  '
            f'DT{row["daytype"]:<5}  {row["representative_date"]}  '
            f'{row["num_trips"]:>5}  {row["num_dates"]:>5}'
        )


def _write_calendar(rows: list[dict[str, object]], path: Path) -> None:
    """Write date-to-DayType calendar rows.

    :param rows: Calendar rows.
    :param path: Output CSV path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        fieldnames = ['date', 'weekday', 'daytype', 'representative_date', 'num_trips', 'num_dates']
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _inspect_route_patterns(
    feed: str,
    *,
    route_id: str,
    shape_ids: list[str],
    h3_resolution: int,
    key_method: str,
) -> list[dict[str, object]]:
    """Inspect Route Pattern keys for trips on a route.

    :param feed: Path to a GTFS feed.
    :param route_id: GTFS ``route_id`` to inspect.
    :param shape_ids: Optional shape-id filter.
    :param h3_resolution: H3 resolution used for Route Pattern keys.
    :param key_method: ``h3`` for H3 keys or ``stop_ids`` for direct stop-id keys.
    :returns: Inspection rows.
    """
    trips = read_gtfs_table(feed, 'trips.txt')
    stop_times = read_gtfs_table(feed, 'stop_times.txt')
    stops = read_gtfs_table(feed, 'stops.txt')
    patterns = build_route_patterns(
        trips,
        stop_times,
        stops,
        h3_resolution=h3_resolution,
        key_method=key_method,
    )
    shape_filter = set(shape_ids)
    rows = []
    for trip in trips:
        if trip.get('route_id') != route_id:
            continue
        if shape_filter and trip.get('shape_id') not in shape_filter:
            continue
        pattern = patterns[trip['trip_id']]
        rows.append(
            {
                'trip_id': trip['trip_id'],
                'route_id': trip.get('route_id', ''),
                'shape_id': trip.get('shape_id', ''),
                'direction_id': trip.get('direction_id', ''),
                'pattern': pattern.key,
                'num_stops': len(pattern.stop_ids),
            }
        )
    return rows


def _write_inspection(rows: list[dict[str, object]], path: Path) -> None:
    """Write Route Pattern inspection rows.

    :param rows: Inspection rows.
    :param path: Output CSV path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        fieldnames = ['trip_id', 'route_id', 'shape_id', 'direction_id', 'pattern', 'num_stops']
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _print_inspection_summary(rows: list[dict[str, object]]) -> None:
    """Print Route Pattern inspection summary.

    :param rows: Inspection rows.
    """
    if not rows:
        print('No trips matched the requested route/shape filters.')
        return

    by_shape = {}
    by_pattern = {}
    for row in rows:
        shape_id = str(row['shape_id'])
        pattern = str(row['pattern'])
        by_shape[shape_id] = by_shape.get(shape_id, 0) + 1
        by_pattern.setdefault(pattern, set()).add(shape_id)

    print(f'Matched trips: {len(rows)}')
    print('Trips by shape_id:')
    for shape_id, count in sorted(by_shape.items()):
        print(f'  {shape_id}: {count}')
    print(f'Route Pattern keys: {len(by_pattern)}')
    for pattern, shape_ids in sorted(by_pattern.items()):
        print(f'  {pattern}: shape_ids={", ".join(sorted(shape_ids))}')
