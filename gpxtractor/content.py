import itertools
from datetime import timedelta
import numpy as np
import pandas as pd
from pandas.api.types import is_integer_dtype

import gpxtractor
from gpxtractor.area_graphs import draw_all_area_charts_for_x
from gpxtractor.tables import create_splits_table, create_summary_table
from gpxtractor.ansi_styling import (
    style_text,
    len_ansifree,
    centre_ansifree,
    rjust_ansifree,
    ljust_ansifree,
)


TITLE = """

█▀▀▀ █▀▀█ ▀▄ ▄▀ ▀▀█▀▀ █▀▀█ █▀▀█ █▀▀ ▀▀█▀▀ █▀▀█ █▀▀█
█ ▀█ █▀▀▀  ▄▀▄    █   █▀█▀ █▀▀█ █     █   █  █ █▀█▀
▀▀▀▀ ▀    ▀   ▀   ▀   ▀ ▀▀ ▀  ▀ ▀▀▀   ▀   ▀▀▀▀ ▀ ▀▀
"""
INSTRUCTIONS = "PRESS 1 FOR CHARTS, 2 FOR KILOMETRE SPLITS, 3 FOR LAPS"
INSTRUCTIONS_CHARTS = "PRESS l FOR DISTANCE ON X-AXIS, h FOR TIME ON X-AXIS"
KM_SPLITS_TITLE = r"""
_  _ _ _    ____ _  _ ____ ___ ____ ____    ____ ___  _    _ ___ ____
|_/  | |    |  | |\/| |___  |  |__/ |___    [__  |__] |    |  |  [__
| \_ | |___ |__| |  | |___  |  |  \ |___    ___] |    |___ |  |  ___]
"""
LAPS_TITLE = r"""
_    ____ ___  ____
|    |__| |__] [__
|___ |  | |    ___]
"""


def titlefonts_to_lines(text: str) -> list[str]:
    lines = text.split("\n")
    max_length = max(len_ansifree(line) for line in lines)

    output = []
    for line in lines:
        output.append(f"{ljust_ansifree(line, max_length)}")
    return output


def create_page_header(activity: gpxtractor.Activity):
    output = []
    for line in titlefonts_to_lines(TITLE):
        line = style_text(line, colour="blue")
        output.append(line)
    summary_table = create_summary_table(activity)
    output += summary_table
    output.append(INSTRUCTIONS)
    return output


def get_km_table(activity):
    output = titlefonts_to_lines(KM_SPLITS_TITLE)
    output += create_splits_table(activity.km_splits, activity.sport)
    return output


def get_lap_table(activity):
    output = titlefonts_to_lines(LAPS_TITLE)
    lap_table = ["No lap data"]
    if activity.lap_splits is not None:
        lap_table = create_splits_table(activity.lap_splits, activity.sport)
    output += lap_table
    return output


def create_pages(activity: gpxtractor.Activity):
    page_1_time = []
    page_1_distance = []
    page_2 = []
    page_3 = []
    pages = [page_1_time, page_1_distance, page_2, page_3]
    page_header = create_page_header(activity)
    for page in pages:
        page += page_header

    page_1_time.append(INSTRUCTIONS_CHARTS)
    page_1_distance.append(INSTRUCTIONS_CHARTS)
    page_1_time += draw_all_area_charts_for_x(activity, "elapsed_time")
    page_1_distance += draw_all_area_charts_for_x(activity, "distance")

    page_2 += get_km_table(activity)
    page_3 += get_lap_table(activity)
    return pages
