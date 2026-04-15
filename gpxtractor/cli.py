#!/usr/bin/env python

import argparse
import visidata

from gpxtractor import extract_data


def parse_args():
    parser = argparse.ArgumentParser(
        description="Display a GPX or TCX file as a dataframe in visidata."
    )
    parser.add_argument("file", type=str, help="")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Display the raw data as in the file with no transformation.",
    )
    parser.add_argument(
        "--sport",
        action="store_true",
        help="Print the sport or activity type of the file.",
    )
    parser.add_argument(
        "--km_splits",
        action="store_true",
        help="Display aggregated stats grouped by kilometer.",
    )
    parser.add_argument(
        "--lap_splits",
        action="store_true",
        help="Display aggregated stats grouped by lap.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    activity = extract_data(file_path=args.file)
    if args.raw:
        visidata.vd.view_pandas(df=activity.records)
        return

    activity.full_transform()

    if args.sport:
        print(activity.sport)
    elif args.km_splits:
        visidata.vd.view_pandas(df=activity.km_splits)
    elif args.lap_splits:
        if activity.lap_splits is not None:
            visidata.vd.view_pandas(df=activity.lap_splits)
        else:
            print("No laps in file")
    else:
        visidata.vd.view_pandas(df=activity.records)


if __name__ == "__main__":
    main()
