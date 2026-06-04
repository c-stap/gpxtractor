import gpxtractor
from gpxtractor._tui.area_graphs import draw_all_area_charts_for_x
from gpxtractor._tui.tables import create_splits_table, create_summary_table
from gpxtractor._tui.ansi_styling import (
    style_text,
    len_ansifree,
    ljust_ansifree,
)


TITLE = """

█▀▀▀ █▀▀█ ▀▄ ▄▀ ▀▀█▀▀ █▀▀█ █▀▀█ █▀▀ ▀▀█▀▀ █▀▀█ █▀▀█
█ ▀█ █▀▀▀  ▄▀▄    █   █▀█▀ █▀▀█ █     █   █  █ █▀█▀
▀▀▀▀ ▀    ▀   ▀   ▀   ▀ ▀▀ ▀  ▀ ▀▀▀   ▀   ▀▀▀▀ ▀ ▀▀
"""
INSTRUCTIONS = "PRESS 1 FOR CHARTS, 2 FOR KILOMETRE SPLITS, 3 FOR LAPS"
INSTRUCTIONS_CHARTS = "PRESS l FOR DISTANCE ON X-AXIS, h FOR TIME ON X-AXIS"

# Following font 'cybermedium' generated with `art` python library
KM_SPLITS_TITLE = r"""
_  _ _ _    ____ _  _ ____ ___ ____ ____    ____ ___  _    _ ___ ____
|_/  | |    |  | |\/| |___  |  |__/ |___    [__  |__] |    |  |  [__
| \_ | |___ |__| |  | |___  |  |  \ |___    ___] |    |___ |  |  ___]
"""
MILE_SPLITS_TITLE = r"""
_  _ _ _    ____    ____ ___  _    _ ___ ____
|\/| | |    |___    [__  |__] |    |  |  [__
|  | | |___ |___    ___] |    |___ |  |  ___]
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


def get_splits_table(activity):
    title = KM_SPLITS_TITLE
    if activity.units.get("unit_system") == "imperial":
        title = MILE_SPLITS_TITLE
    output = titlefonts_to_lines(title)
    output += create_splits_table(activity, "splits")
    return output


def get_lap_table(activity):
    output = titlefonts_to_lines(LAPS_TITLE)
    lap_table = ["No lap data"]
    if activity.laps is not None:
        lap_table = create_splits_table(activity, "laps")
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

    page_2 += get_splits_table(activity)
    page_3 += get_lap_table(activity)
    return pages
