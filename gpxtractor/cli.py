#!/usr/bin/env python

import argparse
import visidata

import gpxtractor
from gpxtractor import extract_data


def parse_args():
    parser = argparse.ArgumentParser(
        description="Display a GPX or TCX file as a dataframe in visidata."
    )
    parser.add_argument("file", type=str, nargs="?", help="")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Display the data from the file with no transformation in a table.",
    )
    parser.add_argument(
        "--sport",
        action="store_true",
        help="Print the sport or activity type of the file.",
    )
    parser.add_argument(
        "--kms",
        action="store_true",
        help="Display aggregated stats grouped by kilometer.",
    )
    parser.add_argument(
        "--laps",
        action="store_true",
        help="Display aggregated stats grouped by lap.",
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
    elif args.kms:
        visidata.vd.view_pandas(df=activity.km_splits)
    elif args.laps:
        if activity.lap_splits is not None:
            visidata.vd.view_pandas(df=activity.lap_splits)
        else:
            print("No laps in file")
    else:
        visidata.vd.view_pandas(df=activity.records)


if __name__ == "__main__":
    main()
