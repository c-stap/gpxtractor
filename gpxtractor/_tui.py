import itertools
from datetime import timedelta
import numpy as np
import pandas as pd
from pandas.api.types import is_integer_dtype
from rich.text import Text
from rich.table import Table
from rich.console import Group
from rich.align import Align
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static, Footer
from textual.binding import Binding

import gpxtractor
from gpxtractor._transformation import bin_records_by_distance, bin_records_by_time


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


def area_chart_2(data: pd.Series, miny, maxy, height_ndots, width_ndots):
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


def draw_area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    y_unit: str,
    colour: str,
    height_nlines: int = 10,
    width_nchar: int = 100,
    ytick_nchar: int = 6,
    ytick_decimals: int = 1,
) -> Align:
    # Char resolution to braille dot resolution
    width_ndots = width_nchar * 2
    height_ndots = height_nlines * 4
    total_width_nchar = width_nchar + ytick_nchar + 1

    if x == "elapsed_time":
        df = bin_records_by_time(df, n_bins=width_ndots)
        x_label = "Elapsed time"
        x_unit = "(HH:MM:SS)"
    elif x == "distance":
        df = bin_records_by_distance(df, n_bins=width_ndots)
        x_label = "Distance"
        x_unit = "km"
    data = df[y]

    output = Text("")
    if not (data == 0).all() and ~data.isna().all():
        maxy = data.max()
        miny = data.min()
        miny_tick = f"{miny:>{ytick_nchar}.{ytick_decimals}f}"
        maxy_tick = f"{maxy:>{ytick_nchar}.{ytick_decimals}f}"
        if is_integer_dtype(data):
            miny_tick = f"{miny:>{ytick_nchar}}"
            maxy_tick = f"{maxy:>{ytick_nchar}}"

        output = Text()
        title = Text(
            "\n" + title + trail_blanks(title, total_width_nchar), style="bold"
        )
        output.append(title)
        output.append("\n" + y_unit + trail_blanks(y_unit, total_width_nchar))

        area_lines = area_chart_2(data, miny, maxy, height_ndots, width_ndots)
        for i, line in enumerate(area_lines):
            text = Text.assemble(f"\n{' ' * ytick_nchar}│", (line, colour))
            if i == 0:
                text = Text.assemble(f"\n{maxy_tick}│", (line, colour))
            output.append(text)
        output.append(f"\n{miny_tick}└" + ("┬" + "─" * 19) * 5)

        xticks = []
        start_x = df[x].at[0]
        for xtick in df[x].iloc[1 :: int(width_ndots / 5)]:
            xtick_str = f"{xtick:.2f}"
            if x == "elapsed_time":
                xtick_str = str(timedelta(seconds=xtick))
            xticks.append(xtick_str)
        xticks_str = chr(EMPTY_BRAILLE_CHAR) * (ytick_nchar + 1)
        xticks_str += "".join(
            tick + chr(EMPTY_BRAILLE_CHAR) * (20 - len(tick)) for tick in xticks
        )
        output.append("\n" + xticks_str)

        len_x_label_unit = len(x_label) + 1 + len(x_unit)
        x_label_line = Text.assemble(
            "\n",
            chr(EMPTY_BRAILLE_CHAR) * (total_width_nchar - len_x_label_unit),
            (x_label, "bold"),
            " ",
            x_unit,
        )
        output.append(x_label_line)

    return Align.center(output)


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


def splits_table(df: pd.DataFrame, sport: str) -> Align:
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

    return Align.center(table)


def summary_table(activity: gpxtractor.Activity) -> Table:
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
    table = Table(show_header=False)
    table.add_column(justify="right", style="bold")
    table.add_column()
    for stat in stats:
        table.add_row(*stat)
    return table


def cli_dashboard(activity: gpxtractor.Activity, x):
    if not activity.is_transformed:
        activity.full_transform()

    title = Align.center(Text(TITLE, style="blue"))
    summary = Align.center(summary_table(activity))
    cadence_unit = "spm" if activity.sport == "running" else "rpm"
    elev_chart = draw_area_chart(
        activity.records,
        x,
        "altitude",
        "Elevation",
        "m",
        "white",
    )
    speed_chart = draw_area_chart(
        activity.records,
        x,
        "speed",
        "Speed",
        "km/h",
        "blue",
    )
    hr_chart = draw_area_chart(
        activity.records,
        x,
        "heart_rate",
        "Heart Rate",
        "bpm",
        "red",
    )
    cadence_chart = draw_area_chart(
        activity.records,
        x,
        "cadence",
        "Cadence",
        cadence_unit,
        "green",
    )
    km_table = splits_table(activity.km_splits, activity.sport)
    lap_table = ""
    if activity.lap_splits is not None:
        lap_table = splits_table(activity.lap_splits, activity.sport)

    output = Group(
        title,
        summary,
        elev_chart,
        speed_chart,
        hr_chart,
        cadence_chart,
        km_table,
        lap_table,
    )

    return output


def get_km_table(activity):
    return splits_table(activity.km_splits, activity.sport)


def get_lap_table(activity):
    lap_table = ""
    if activity.lap_splits is not None:
        lap_table = splits_table(activity.lap_splits, activity.sport)
    return lap_table


class GPXtractorTUI(App):
    """A Textual app with pager-like keybindings."""

    BINDINGS = [
        Binding("j,down,enter", "scroll_down", "Scroll Down", show=True),
        Binding("k,up,backspace", "scroll_up", "Scroll Up", show=True),
        Binding("h", "toggle('view1')", "Time on X-axis", show=True),
        Binding("l", "toggle('view2')", "Distance on X-axis", show=True),
        Binding("f,space", "page_down", "Page Down", show=True),
        Binding("b", "page_up", "Page Up", show=True),
        Binding("g", "top", "Top", show=True),
        Binding("G", "bottom", "Bottom", show=True),
        Binding("q,escape", "quit", "Quit", show=True),
    ]

    def __init__(self, activity: gpxtractor.Activity):
        super().__init__()
        self.content1 = cli_dashboard(activity, "elapsed_time")
        self.content2 = cli_dashboard(activity, "distance")

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="scroll_window"):
            self.view1 = Static(id="view1", expand=True)
            yield self.view1
            self.view2 = Static(id="view", expand=True)
            self.view2.styles.display = "none"
            yield self.view2
        yield Footer(show_command_palette=False)

    async def on_mount(self):
        self.view1.update(self.content1)
        self.view2.update(self.content2)

    def action_toggle(self, view: str) -> None:
        if view == "view1":
            self.view1.styles.display = "block"
            self.view2.styles.display = "none"
        else:
            self.view1.styles.display = "none"
            self.view2.styles.display = "block"

    def action_scroll_down(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_down()

    def action_scroll_up(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_up()

    def action_page_down(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_page_down()

    def action_page_up(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_page_up()

    def action_top(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_home()

    def action_bottom(self) -> None:
        self.query_one("#scroll_window", VerticalScroll).scroll_end()
