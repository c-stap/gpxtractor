#!/usr/bin/env python

import argparse
import visidata

import gpxtractor
from gpxtractor import extract_data
from gpxtractor._tui import GPXtractorTUI


def parse_args():
    parser = argparse.ArgumentParser(
        description="""
            Data extraction and transformation for gpx, tcx and fit.
            By default, presents an overview of the data with aggregate stats
            and data visuals.
            """
    )
    parser.add_argument("file", type=str, nargs="?", help="")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Display the data as extracted in visidata.",
    )
    parser.add_argument(
        "--transform",
        action="store_true",
        help="Display the data transformed in visidata.",
    )
    parser.add_argument(
        "--sport",
        action="store_true",
        help="Print the sport or activity type of the file.",
    )
    parser.add_argument(
        "--kms",
        action="store_true",
        help="Display aggregated stats grouped by kilometer in visidata.",
    )
    parser.add_argument(
        "--laps",
        action="store_true",
        help="Display aggregated stats grouped by lap in visidata.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Display version and exit.",
    )

    return parser, parser.parse_args()


def main():
    parser, args = parse_args()

    if args.version:
        print(f"gpxtractor v{gpxtractor.__version__}")
        return

    if not args.file and not args.version:
        parser.error("the following arguments are required: file")

    activity = extract_data(file_path=args.file)
    if args.raw:
        visidata.vd.view_pandas(df=activity.records)
        return

    activity.full_transform()

    if args.sport:
        print(activity.sport)
    elif args.transform:
        visidata.vd.view_pandas(df=activity.records)
    elif args.kms:
        visidata.vd.view_pandas(df=activity.km_splits)
    elif args.laps:
        if activity.lap_splits is not None:
            visidata.vd.view_pandas(df=activity.lap_splits)
        else:
            print("No laps in file")
    else:
        app = GPXtractorTUI(activity)
        app.run()


if __name__ == "__main__":
    main()
