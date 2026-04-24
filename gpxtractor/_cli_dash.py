import itertools
import pandas as pd

import gpxtractor


EMPTY_BRAILLE_CHAR = 0x2800
FULL_BRAILLE_CHAR = 0x28FF

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

    value = sum((1 << i) for i, d in enumerate(dots) if d)

    return chr(EMPTY_BRAILLE_CHAR + value)


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


def chart(data: pd.Series, colour):
    if (data == 0).all():
        return

    N_BARS = 200
    n_data_points = len(data)
    if n_data_points > 200:
        step = n_data_points // N_BARS
    else:
        step = 1
    max_val = data.max()
    data_range = data.max() - data.min()
    miny_buffer = data.min() - data_range * 0.05
    transformed_data = []
    if max_val != 0:
        for item in data.iloc[::step]:
            item_transformed = int((item - miny_buffer) / (max_val - miny_buffer) * 40)
            transformed_data.append(item_transformed)

    print_colour(braille_columns(transformed_data), colour)


def cli_dashboard(activity: gpxtractor.Activity):
    if not activity.is_transformed:
        activity.full_transform()

    print(TITLE)

    print("Elevation")
    print("=========")
    chart(activity.records["altitude"], "grey")

    print("Speed")
    print("=====")
    chart(activity.records["speed"], "cyan")

    print("Heart Rate")
    print("==========")
    chart(activity.records["heart_rate"], "pink")

    print("Cadence")
    print("=======")
    chart(activity.records["cadence"], "green")
