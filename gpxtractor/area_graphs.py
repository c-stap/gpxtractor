import itertools
from datetime import timedelta
import pandas as pd
import numpy as np
from pandas.api.types import is_integer_dtype

import gpxtractor
from gpxtractor.ansi_styling import style_text
from gpxtractor._transformation import bin_records_by_distance, bin_records_by_time


EMPTY_BRAILLE_CHAR = 0x2800
FULL_BRAILLE_CHAR = 0x28FF


def braille_char(left: int, right: int) -> str:
    left = min(left, 4)
    right = min(right, 4)

    left = 0 if left < 0 else left
    right = 0 if right < 0 else right

    left_dots = [0] * (4 - left) + [1] * left
    right_dots = [0] * (4 - right) + [1] * right

    # Unicode position left (top to bottom) 1, 2, 3, 7
    # Unicode position right (top to bottom) 4, 5, 6, 8
    dot_positions = [0, 1, 2, 6, 3, 4, 5, 7]
    dots = [0] * 8
    for dot, position in zip(left_dots + right_dots, dot_positions):
        dots[position] = dot

    bit_diff = sum((1 << i) for i, d in enumerate(dots) if d)

    return chr(EMPTY_BRAILLE_CHAR + bit_diff)


def braille_columns(data: list[int]) -> str:
    max_val = max(data)
    n_lines = max_val // 4 + 1 if max_val % 4 else max_val // 4
    lines = []
    amount_plotted = 0
    for i in range(n_lines):
        line = []
        for left_col, right_col in itertools.zip_longest(
            data[::2], data[1::2], fillvalue=0
        ):
            left = left_col - amount_plotted
            right = right_col - amount_plotted
            # left = 0 if left < 0 else left
            # right = 0 if right < 0 else right

            if left >= 4 and right >= 4:
                line.append(chr(FULL_BRAILLE_CHAR))
            else:
                line.append(braille_char(left, right))

        line = "".join(char for char in line)
        lines.insert(0, line)
        amount_plotted += 4
    return lines


def area_chart(data: pd.Series, miny, maxy, height_ndots, width_ndots):
    if (data == 0).all():
        return

    data_range = maxy - miny
    miny_buffer = miny - data_range * 0.05
    transformed_data = []
    if maxy != 0:
        for item in data:
            item_transformed = 0
            if item is not None and ~np.isnan(item):
                item_transformed = int(
                    (item - miny_buffer) / (maxy - miny_buffer) * height_ndots
                )
            transformed_data.append(item_transformed)

    return braille_columns(transformed_data)


def trail_blanks(text: str, line_nchar: int) -> str:
    return chr(EMPTY_BRAILLE_CHAR) * (line_nchar - len(text))


# TODO: make each string in ouput_lines have the same length (ansifree)
def draw_area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    y_label: str,
    y_unit: str,
    colour: str,
    height_nlines: int = 10,
    width_nchar: int = 100,
    ytick_nchar: int = 6,
    ytick_decimals: int = 1,
) -> list[str]:
    # Char resolution to braille dot resolution
    width_ndots = width_nchar * 2
    height_ndots = height_nlines * 4
    total_width_nchar = width_nchar + ytick_nchar + 1

    if x == "elapsed_time":
        x_label = "Elapsed time"
        x_unit = "(HH:MM:SS)"
    elif x == "distance":
        x_label = "Distance"
        x_unit = "km"
    data = df[y]

    if not (data == 0).all() and ~data.isna().all():
        maxy = data.max()
        miny = data.min()
        miny_tick = f"{miny:>{ytick_nchar}.{ytick_decimals}f}"
        maxy_tick = f"{maxy:>{ytick_nchar}.{ytick_decimals}f}"
        if is_integer_dtype(data):
            miny_tick = f"{miny:>{ytick_nchar}}"
            maxy_tick = f"{maxy:>{ytick_nchar}}"

        output_lines = [""]
        y_label = style_text(y_label, style="bold") + trail_blanks(
            y_label, total_width_nchar
        )
        output_lines.append(y_label)
        y_unit_line = y_unit + trail_blanks(y_unit, total_width_nchar)
        output_lines.append(y_unit_line)

        area_lines = area_chart(data, miny, maxy, height_ndots, width_ndots)
        for i, line in enumerate(area_lines):
            text = f"{' ' * ytick_nchar}│" + style_text(line, colour=colour)
            if i == 0:
                text = f"{maxy_tick}│" + style_text(line, colour=colour)
            text += trail_blanks(text, total_width_nchar)
            output_lines.append(text)
        x_axis_str = (
            f"{miny_tick}└" + ("┬" + "─" * 19) * 5 + "─"
        )  # TODO: last char is a bodged fix
        output_lines.append(x_axis_str)

        xticks = []
        for xtick in df[x].iloc[1 :: int(width_ndots / 5)]:
            xtick_str = f"{xtick:.2f}"
            if x == "elapsed_time":
                xtick_str = str(timedelta(seconds=xtick))
            xticks.append(xtick_str)
        xticks_str = chr(EMPTY_BRAILLE_CHAR) * (ytick_nchar + 1)
        xticks_str += "".join(
            tick + chr(EMPTY_BRAILLE_CHAR) * (20 - len(tick)) for tick in xticks
        )
        xticks_str += trail_blanks(xticks_str, total_width_nchar)
        output_lines.append(xticks_str)

        len_x_label_unit = len(x_label) + 1 + len(x_unit)
        x_label_line = (
            chr(EMPTY_BRAILLE_CHAR) * (total_width_nchar - len_x_label_unit)
            + style_text(x_label, style="bold")
            + " "
            + x_unit
        )
        x_label_line += trail_blanks(x_label_line, total_width_nchar)
        output_lines.append(x_label_line)

        return output_lines


def draw_all_area_charts_for_x(
    activity: gpxtractor.Activity,
    x: str,
    height_nlines: int = 10,
    width_nchar: int = 100,
    ytick_nchar: int = 6,
    ytick_decimals: int = 1,
) -> list[str]:

    width_ndots = width_nchar * 2
    if x == "elapsed_time":
        df = bin_records_by_time(activity.records, n_bins=width_ndots)
    elif x == "distance":
        df = bin_records_by_distance(activity.records, n_bins=width_ndots)

    cadence_unit = "rpm"
    if activity.sport == "running":
        cadence_unit = "spm"

    output_lines = []
    y_colours = [None, "blue", "red", "green"]
    y_variables = ["altitude", "speed", "heart_rate", "cadence"]
    y_units = ["m", "km/h", "bpm", cadence_unit]
    for y, colour, unit in zip(y_variables, y_colours, y_units):
        if not df[y].isna().all() and df[y].all() != 0:
            chart_lines = draw_area_chart(
                df,
                x,
                y,
                y_label=y.capitalize(),
                y_unit=unit,
                colour=colour,
                height_nlines=height_nlines,
                width_nchar=width_nchar,
                ytick_nchar=ytick_nchar,
                ytick_decimals=ytick_decimals,
            )
            output_lines.extend(chart_lines)
    return output_lines
