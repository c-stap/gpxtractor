#!/usr/bin/env python

import argparse
import visidata

import gpxtractor
from gpxtractor.content import create_pages
import gpxtractor.tui_framework as tui


def parse_args():
    parser = argparse.ArgumentParser(
        description="""
            Data extraction and transformation for gpx, tcx and fit.
            By default, opens a Terminal User Interface (TUI) of the data
            with aggregate stats and data visuals.
            """
    )
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        help="Input file (required for default usage, except with --version or --help).",
    )
    parser.add_argument(
        "--imperial",
        action="store_true",
        help="Use imperial units instead of default metric system.",
    )
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
        help="Display the sport or activity type of the file.",
    )
    parser.add_argument(
        "--splits",
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

    activity = gpxtractor.extract_data(file_path=args.file)
    if args.raw:
        visidata.vd.view_pandas(df=activity.records)
        return

    if args.imperial:
        activity.full_transform(units="imperial")
    else:
        activity.full_transform()

    if args.sport:
        print(activity.sport)
    elif args.transform:
        visidata.vd.view_pandas(df=activity.records)
    elif args.splits:
        visidata.vd.view_pandas(df=activity.splits)
    elif args.laps:
        if activity.laps is not None:
            visidata.vd.view_pandas(df=activity.laps)
        else:
            print("No laps in file")
    else:
        pages = create_pages(activity)
        del activity
        tui.run(*pages)


if __name__ == "__main__":
    main()
