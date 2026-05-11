from datetime import timedelta
import pandas as pd

import gpxtractor
from gpxtractor.ansi_styling import (
    style_text,
    len_ansifree,
    centre_ansifree,
    rjust_ansifree,
    ljust_ansifree,
)


FULL_BLOCK_CHAR = 0x2588

HORIZONTAL = "─"
VERTICAL = "│"
TOP_LEFT = "┌"
TOP_RIGHT = "┐"
BOTTOM_LEFT = "└"
BOTTOM_RIGHT = "┘"
INTERSECT = "┼"
TOP_INTERSECT = "┬"
BOTTOM_INTERSECT = "┴"
RIGHT_INTERSECT = "┤"
LEFT_INTERSECT = "├"


def block_char(x: int) -> str:
    x = min(x, 8)
    x = max(x, 0)
    block = " "
    if x != 0:
        bit_diff = 8 - x
        block = chr(FULL_BLOCK_CHAR + bit_diff)
    return block


def horizontal_bar(value, total, char_length: int) -> str:
    if char_length > 0 and isinstance(char_length, int):
        if value <= total:
            # Block characters allow for x8 definition
            full_def_length = char_length * 8
            transformed_value = int(round(value / total * full_def_length))
            n_full_blocks = transformed_value // 8
            extra_char = block_char(transformed_value % 8)
            empty_spaces = " " * (char_length - n_full_blocks - 1)
            return chr(FULL_BLOCK_CHAR) * n_full_blocks + extra_char + empty_spaces
        else:
            raise ValueError(
                "value param must be equal or less than equal to total param"
            )
    else:
        raise ValueError("char_length must be integer superior to 0")


# TODO: refactor: extract each step
def create_table(data: list[list], headers: list = None, align: list = None):
    output_lines = []

    if align is None:
        align = ["left"] * len(data[0])
    if len(align) != len(data[0]):
        raise ValueError("Length of 'align' must match number of headers")

    col_widths = [max(len_ansifree(str(item)) for item in col) for col in zip(*data)]
    if headers is not None:
        header_lines = [h.split("\n") for h in headers]
        max_header_lines = max(len(lines) for lines in header_lines)

        for lines in header_lines:
            while len(lines) < max_header_lines:
                lines.append("")

        col_widths = [
            max(
                max(len_ansifree(str(line)) for line in lines),
                max(len_ansifree(str(item)) for item in col),
            )
            for lines, col in zip(header_lines, zip(*data))
        ]

    top_border = TOP_LEFT
    for i, width in enumerate(col_widths):
        top_border += HORIZONTAL * (width + 2)
        top_border += TOP_INTERSECT if i < len(col_widths) - 1 else TOP_RIGHT
    output_lines.append(top_border)

    if headers is not None:
        for line_idx in range(max_header_lines):
            row = VERTICAL
            for i, (lines, width) in enumerate(zip(header_lines, col_widths)):
                line = lines[line_idx]
                row += f" {ljust_ansifree(line, width)} " + VERTICAL
            output_lines.append(row)

        separator = LEFT_INTERSECT
        for i, width in enumerate(col_widths):
            separator += HORIZONTAL * (width + 2)
            separator += INTERSECT if i < len(col_widths) - 1 else RIGHT_INTERSECT
        output_lines.append(separator)

    for row_data in data:
        row = VERTICAL
        for i, (item, width) in enumerate(zip(row_data, col_widths)):
            alignment = align[i]
            if alignment == "left":
                formatted = f" {ljust_ansifree(str(item), width)} "
            elif alignment == "centre":
                formatted = f" {centre_ansifree(str(item), width)} "
            elif alignment == "right":
                formatted = f" {rjust_ansifree(str(item), width)} "
            else:
                raise ValueError(
                    f"Invalid alignment: {alignment}. Use 'left', 'centre', or 'right'."
                )
            row += formatted + VERTICAL
        output_lines.append(row)

    bottom_border = BOTTOM_LEFT
    for i, width in enumerate(col_widths):
        bottom_border += HORIZONTAL * (width + 2)
        bottom_border += BOTTOM_INTERSECT if i < len(col_widths) - 1 else BOTTOM_RIGHT
    output_lines.append(bottom_border)

    return output_lines


def get_headers(sport: str):
    headers = [
        style_text("Split", style="bold"),
        style_text("Distance", style="bold") + "\n(km)",
        style_text("Average Speed", style="bold") + "\n(km/h)",
        style_text("Elev +", style="bold") + "\n(m)",
        style_text("Elev -", style="bold") + "\n(m)",
        style_text("Average HR", style="bold") + "\n(bpm)",
        style_text("Average Cadence", style="bold") + "\n(rpm)",
    ]

    if sport == "running":
        headers[2] = style_text("Average Pace", style="bold") + "\n(min/km)"
        headers[-1] = style_text("Average Cadence", style="bold") + "\n(spm)"
    return headers


def colour_bar(bar_str: str, col: str):
    match col:
        case "avg_speed_kph":
            bar_str = style_text(bar_str, colour="blue")
        case "avg_hr":
            bar_str = style_text(bar_str, colour="red")
        case "avg_cadence":
            bar_str = style_text(bar_str, colour="green")
    return bar_str


def get_rows(df: pd.DataFrame, sport: str):
    columns_to_include = {
        "avg_speed_kph": ">6.2f",
        "elevation_gain": ">4",
        "elevation_loss": ">4",
        "avg_hr": ">3",
        "avg_cadence": ">3",
    }

    max_values = {col: df[col].max() for col in columns_to_include}

    table_rows = []
    for row in df.itertuples(index=False):
        split = str(row[0])
        distance = f"{round(row.distance, 2):.2f}"
        row_elements = [split, distance]
        for col, fmt in columns_to_include.items():
            value = getattr(row, col)

            formatted_value = f"{value:{fmt}}"
            if col == "avg_speed_kph" and sport == "running":
                formatted_value = f"{row.avg_pace:>6}"

            element_string = "No Data"
            if value is not None and max_values[col] > 0:
                bar_str = horizontal_bar(value, max_values[col], 12)
                bar_str = colour_bar(bar_str, col)
                element_string = formatted_value + " " + bar_str
            row_elements.append(element_string)

        table_rows.append(row_elements)

    return table_rows


def create_splits_table(df: pd.DataFrame, sport: str):
    headers = get_headers(sport)
    rows = get_rows(df, sport)
    align = ["right", "right", "left", "left", "left", "left", "left"]
    table = create_table(rows, headers, align)
    return table


def create_summary_table(activity: gpxtractor.Activity) -> list[str]:
    cadence_unit = "spm" if activity.sport == "running" else "rpm"
    stats = [
        ["Sport", activity.sport],
        ["Start time", str(activity.start_time)],
        ["Distance", f"{activity.distance:.2f} km"],
        ["Elapsed Time", str(timedelta(seconds=activity.elapsed_time))],
        ["Elevation Gain", f"{activity.elevation_gain} m"],
        ["Elevation Loss", f"{activity.elevation_loss} m"],
        ["Average pace", f"{activity.avg_pace} min/km"],
        ["Average speed", f"{activity.avg_speed:.2f} km/h"],
        ["Maximum speed", f"{activity.max_speed:.2f} km/h"],
    ]
    if activity.sport in ["cycling", "biking"]:
        stats.pop(6)
    if activity.avg_heart_rate != 0:
        stats += [
            ("Average heart rate", f"{activity.avg_heart_rate} bpm"),
            ("Maximum heart rate", f"{activity.max_heart_rate} bpm"),
        ]

    if activity.avg_cadence != 0:
        stats += [
            ("Average cadence", f"{activity.avg_cadence} {cadence_unit}"),
            ("Maximum cadence", f"{activity.max_cadence} {cadence_unit}"),
        ]
    table = create_table(stats, align=["right", "left"])
    return table
