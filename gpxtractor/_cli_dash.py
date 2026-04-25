import itertools
from datetime import timedelta
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

import gpxtractor


EMPTY_BRAILLE_CHAR = 0x2800
FULL_BRAILLE_CHAR = 0x28FF

FULL_BLOCK_CHAR = 0x2588

TITLE = """

█▀▀▀ █▀▀█ ▀▄ ▄▀ ▀▀█▀▀ █▀▀█ █▀▀█ █▀▀ ▀▀█▀▀ █▀▀█ █▀▀█
█ ▀█ █▀▀▀  ▄▀▄    █   █▀█▀ █▀▀█ █     █   █  █ █▀█▀
▀▀▀▀ ▀    ▀   ▀   ▀   ▀ ▀▀ ▀  ▀ ▀▀▀   ▀   ▀▀▀▀ ▀ ▀▀
"""


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

        lines.insert(0, line)
        amount_plotted += 4
    return "\n".join("".join(char for char in line) for line in lines)


def braille_cols_with_axes(data: list[int]):
    lines = braille_columns(data)
    return "\n".join("".join(char for char in line) for line in lines)


def print_in_rgb(string: str, r: int, g: int, b: int) -> None:
    print(f"\033[38;2;{r};{g};{b}m{string}\033[0m")


def print_colour(string, colour):
    match colour.lower():
        case "cyan":
            print_in_rgb(string, 8, 199, 247)
        case "pink":
            print_in_rgb(string, 242, 188, 224)
        case "green":
            print_in_rgb(string, 130, 230, 194)
        case _:
            print(string)


def area_chart(data: pd.Series, colour):
    if (data == 0).all():
        return

    N_BARS = 200
    n_data_points = len(data)
    if n_data_points > N_BARS:
        step = n_data_points // N_BARS
    else:
        step = 1
    max_val = data.max()
    data_range = data.max() - data.min()
    miny_buffer = data.min() - data_range * 0.05
    transformed_data = []
    if max_val != 0:
        for item in data.iloc[::step]:
            item_transformed = 0
            if item is not None and ~np.isnan(item):
                item_transformed = int(
                    (item - miny_buffer) / (max_val - miny_buffer) * 40
                )
            transformed_data.append(item_transformed)

    print_colour(braille_columns(transformed_data), colour)


def block_char(x: int) -> str:
    x = min(x, 8)
    x = max(x, 0)
    block = " "
    if x != 0:
        bit_diff = 8 - x
        block = chr(FULL_BLOCK_CHAR + bit_diff)
    return block


def horizontal_bar(value, total, char_length: int):
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


def splits_table(df: pd.DataFrame, sport: str):
    table_title = "Laps" if "lap" in df.columns else "Kilometre Splits"
    table = Table(title=table_title)

    headers = [
        ["Split", "right", None],
        ["Distance\n(km)", "right", None],
        ["Average Speed\n(km/h)", "left", "blue"],
        ["Elevation Gain\n(m)", "left", None],
        ["Elevation Loss\n(m)", "left", None],
        ["Average HR\n(bpm)", "left", "red"],
        ["Average Cadence\n(rpm)", "left", "green"],
    ]
    if sport == "running":
        headers[2][0] = "Average Pace\n(min/km)"
        headers[-1][0] = "Average Cadence\n(spm)"

    for col in headers:
        table.add_column(col[0], justify=col[1], style=col[2])

    # key: column name in df, value: formatting for table
    columns_to_include = {
        "avg_speed_kph": ">6.2f",
        "elevation_gain": ">4",
        "elevation_loss": ">4",
        "avg_hr": ">3",
        "avg_cadence": ">3",
    }

    max_values = {col: df[col].max() for col in columns_to_include}

    for row in df.itertuples():
        split = str(row[1])
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
                element_string = formatted_value + " " + bar_str
            row_elements.append(element_string)

        table.add_row(*row_elements)

    return table


def print_subtitle(subtitle: str):
    print(f"\n{subtitle}\n" + "=" * len(subtitle))


def print_summary(activity: gpxtractor.Activity):
    print_subtitle("ACTIVITY SUMMARY")
    print(f"Sport:              {activity.sport}")
    print(f"Start time:         {activity.start_time}")
    print(f"Distance:           {activity.distance:.2f} km")
    print(f"Elapsed Time:       {str(timedelta(seconds=activity.elapsed_time))}")
    if activity.sport == "running":
        print(f"Average pace:       {activity.avg_pace} min/km")
    print(f"Average speed:      {activity.avg_speed:.2f} km/h")
    print(f"Maximum speed:      {activity.max_speed:.2f} km/h")
    if activity.avg_heart_rate != 0:
        print(f"Average heart rate: {activity.avg_heart_rate} bpm")
        print(f"Maximum heart rate: {activity.max_heart_rate} bpm")
    if activity.avg_cadence != 0:
        cadence_unit = "spm" if activity.sport == "running" else "rpm"
        print(f"Average cadence:    {activity.avg_cadence} {cadence_unit}")
        print(f"Maximum cadence:    {activity.max_cadence} {cadence_unit}")


def cli_dashboard(activity: gpxtractor.Activity):
    if not activity.is_transformed:
        activity.full_transform()

    print(TITLE)
    print_summary(activity)

    print_subtitle("Elevation")
    area_chart(activity.records["altitude"], "grey")

    print_subtitle("Speed")
    area_chart(activity.records["speed"], "cyan")

    print_subtitle("Heart Rate")
    area_chart(activity.records["heart_rate"], "pink")

    print_subtitle("Cadence")
    area_chart(activity.records["cadence"], "green")

    km_table = splits_table(activity.km_splits, activity.sport)
    lap_table = splits_table(activity.lap_splits, activity.sport)

    console = Console()
    console.print(km_table)
    console.print(lap_table)
