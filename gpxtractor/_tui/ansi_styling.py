import re


def style_text(text: str, colour: str = None, style: str = "normal") -> str:
    """
    Style the input text using ANSI escape sequences for colour and style.

    Parameters
    ----------
    text : str
        The text to be styled.
    colour : str
        The colour name (e.g., 'red', 'green') or hex code (e.g., '#FF0000').
    style : str, optional
        The text style: 'bold', 'faint', 'italic', 'underline' or 'normal'
        (default is 'normal').

    Returns
    -------
    str
        The input text wrapped in ANSI escape sequences for the specified
        style.
    """
    colour_map = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }
    style_map = {
        "bold": "1",
        "faint": "2",
        "italic": "3",
        "underline": "4",
        "normal": "0",
    }

    if colour is not None and colour.startswith("#"):
        r, g, b = tuple(int(colour.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        colour_code = f";38;2;{r};{g};{b}"
    elif colour is not None:
        colour_code = ";" + colour_map.get(colour.lower(), "37")
    else:
        colour_code = ""

    style_code = style_map.get(style.lower(), "0")
    return f"\033[{style_code}{colour_code}m{text}\033[0m"


def len_ansifree(text: str) -> int:
    """
    Counts the number of characters in a string excluding
    ANSI escape sequences.
    Identifies ANSI escape sequences using regex.
    """
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\x5B[0-?]*[ -/]*[@-~])")
    cleaned = ansi_escape.sub("", text)
    return len(cleaned)


def centre_ansifree(text: str, width: int) -> str:
    """
    Adds padding to the left and right of a string to centre the text
    in a given width disregarding any ANSI escape sequences
    in the string.
    """
    text_length = len_ansifree(text)
    if text_length < width:
        left_padding = (width - text_length) // 2
        right_padding = width - left_padding - text_length
        text = " " * left_padding + text + " " * right_padding
    return text


def rjust_ansifree(text: str, width: int) -> str:
    """
    Adds padding to the left of a string to right align the text
    in a given width disregarding any ANSI escape sequences
    in the string.
    """
    text_length = len_ansifree(text)
    if text_length < width:
        left_padding = width - text_length
        text = " " * left_padding + text
    return text


def ljust_ansifree(text: str, width: int) -> str:
    """
    Adds padding to the right of a string to left align the text
    in a given width disregarding any ANSI escape sequences
    in the string.
    """

    text_length = len_ansifree(text)
    if text_length < width:
        right_padding = width - text_length
        text = text + " " * right_padding
    return text
