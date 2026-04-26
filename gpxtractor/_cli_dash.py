from io import StringIO
import itertools
from datetime import timedelta
import numpy as np
import pandas as pd
from pandas.api.types import is_integer_dtype
import click
from rich.console import Console
from rich.text import Text
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

        line = "".join(char for char in line)
        lines.insert(0, line)
        amount_plotted += 4
    return lines


def area_chart(data: pd.Series, miny, maxy, height=40, width=200):
    if (data == 0).all():
        return
    n_data_points = len(data)
    step = 1
    if n_data_points > width:
        step = int(round(n_data_points / width))
    data_range = maxy - miny
    miny_buffer = miny - data_range * 0.05
    transformed_data = []
    if maxy != 0:
        for item in data.iloc[::step]:
            item_transformed = 0
            if item is not None and ~np.isnan(item):
                item_transformed = int(
                    (item - miny_buffer) / (maxy - miny_buffer) * height
                )
            transformed_data.append(item_transformed)

    return step, braille_columns(transformed_data)


def draw_area_chart(
    df: pd.DataFrame,
    y: str,
    title: str,
    unit: str,
    colour: str,
    console: Console,
    x: str = "timestamp",
    ytick_nchar: int = 6,
    ytick_decimals: int = 1,
):
    data = df[y]
    if not (data == 0).all() and ~data.isna().all():
        maxy = data.max()
        miny = data.min()
        formatted_miny = f"{miny:>{ytick_nchar}.{ytick_decimals}f}"
        formatted_maxy = f"{maxy:>{ytick_nchar}.{ytick_decimals}f}"
        if is_integer_dtype(data):
            formatted_miny = f"{miny:>{ytick_nchar}}"
            formatted_maxy = f"{maxy:>{ytick_nchar}}"

        title = Text("\n" + title, style="bold")
        unit = Text(unit)
        console.print(title)
        console.print(unit)

        step, lines = area_chart(data, miny, maxy)
        for i, line in enumerate(lines):
            text = Text.assemble(f"{' ' * ytick_nchar}│", (line, colour))
            if i == 0:
                text = Text.assemble(f"{formatted_maxy}│", (line, colour))
            console.print(text)
        console.print(f"{formatted_miny}└" + ("┬" + "─" * 19) * 5, highlight=False)

        xticks = []
        start_x = df[x].at[0]
        for xtick in df[x].iloc[step :: step * 40]:
            if isinstance(xtick, pd.Timestamp):
                time_diff = xtick - start_x
                xtick = time_diff
                hours = time_diff.components.hours
                minutes = time_diff.components.minutes
                seconds = time_diff.components.seconds
                xtick = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                xticks.append(xtick)
        xticks_str = " " * (ytick_nchar + 1)
        xticks_str += "".join(tick + " " * (20 - len(tick)) for tick in xticks)
        console.print(xticks_str, highlight=False)


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


def summary_table(activity: gpxtractor.Activity):
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
        stats.pop(4)
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
    table = Table(show_header=False)
    table.add_column(justify="right", style="bold")
    table.add_column()
    for stat in stats:
        table.add_row(*stat)
    return table


def cli_dashboard(activity: gpxtractor.Activity):
    if not activity.is_transformed:
        activity.full_transform()

    output = StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(TITLE, style="blue", justify="center")
    summary = summary_table(activity)
    console.print(summary, justify="center")

    cadence_unit = "spm" if activity.sport == "running" else "rpm"
    draw_area_chart(
        df=activity.records,
        y="altitude",
        title="Elevation",
        unit="m",
        colour="white",
        console=console,
    )
    draw_area_chart(
        df=activity.records,
        y="speed",
        title="Speed",
        unit="km/h",
        colour="blue",
        console=console,
    )
    draw_area_chart(
        df=activity.records,
        y="heart_rate",
        title="Heart Rate",
        unit="bpm",
        colour="red",
        console=console,
    )
    draw_area_chart(
        df=activity.records,
        y="cadence",
        title="Cadence",
        unit=cadence_unit,
        colour="green",
        console=console,
    )

    km_table = splits_table(activity.km_splits, activity.sport)
    console.print("\n")
    console.print(km_table, justify="center")
    if activity.lap_splits is not None:
        lap_table = splits_table(activity.lap_splits, activity.sport)
        console.print(lap_table, justify="center")

    click.echo_via_pager(output.getvalue())
