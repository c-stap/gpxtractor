import sys
import tty
import termios
import os

from gpxtractor.ansi_styling import centre_ansifree

# TODO: make tui responsive to terminal resizing without having to press key
# TODO: impose minimum width or enable horizontal scrolling


def get_terminal_size():
    return os.get_terminal_size().columns, os.get_terminal_size().lines


def enter_alternate_screen():
    sys.stdout.write("\033[?1049h")
    sys.stdout.flush()


def exit_alternate_screen():
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()


def clear_screen():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def get_lines_to_display(content, top_line, height):
    for i in range(height - 1):
        line_idx = top_line + i
        if line_idx < len(content):
            yield content[line_idx]
        else:
            yield ""


def draw(width, height, content, top_line):
    clear_screen()
    top_line = max(0, min(top_line, len(content) - (height - 1)))
    for line in get_lines_to_display(content, top_line, height):
        sys.stdout.write(f"{centre_ansifree(line, width)}\n")
    sys.stdout.flush()
    return top_line


def handle_key(width, height, content, top_line, current_content):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        match ch:
            case "j":
                if top_line < len(content) - (height - 1):
                    top_line += 1
            case "k":
                if top_line > 0:
                    top_line -= 1
            case "f":
                top_line = min(top_line + height - 1, len(content) - (height - 1))
            case "b":
                top_line = max(top_line - (height - 1), 0)
            case "g":
                top_line = 0
            case "G":
                top_line = max(len(content) - (height - 1), 0)
            case "h":
                if current_content in (0, 1):
                    current_content = 0
            case "l":
                if current_content in (0, 1):
                    current_content = 1
            case "1":
                current_content = 0
                top_line = 0
            case "2":
                current_content = 2
                top_line = 0
            case "3":
                current_content = 3
                top_line = 0
            case "q":
                return top_line, current_content, False
            case "\x03":
                return top_line, current_content, False
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return top_line, current_content, True


def run(content_1, content_2, content_3, content_4):
    width, height = get_terminal_size()
    top_line = 0
    current_content = 0

    enter_alternate_screen()
    clear_screen()
    hide_cursor()

    top_line = draw(width, height, content_1, top_line)

    while True:
        # --- Check for terminal resize ---
        new_width, new_height = get_terminal_size()
        if (new_width, new_height) != (width, height):
            width, height = new_width, new_height
            content = [content_1, content_2, content_3, content_4][current_content]
            top_line = draw(width, height, content, top_line)

        # --- Handle key press ---
        top_line, current_content, should_continue = handle_key(
            width,
            height,
            [content_1, content_2, content_3, content_4][current_content],
            top_line,
            current_content,
        )
        if not should_continue:
            break

        # --- Redraw after key handling ---
        content = [content_1, content_2, content_3, content_4][current_content]
        top_line = draw(width, height, content, top_line)

    show_cursor()
    exit_alternate_screen()
