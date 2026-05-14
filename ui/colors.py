# subtrace/ui/colors.py

from __future__ import annotations


class Colors:
    """
    ANSI color palette for Subtrace CLI.
    """

    RESET = "\033[0m"

    # Basic
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright
    BOLD = "\033[1m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"


def color(text: str, col: str) -> str:
    return f"{col}{text}{Colors.RESET}"
