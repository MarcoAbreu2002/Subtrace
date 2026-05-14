# subtrace/ui/menu.py

from __future__ import annotations

from ui.colors import Colors, color


MENU_ITEMS = [
    ("1", "Passive Discovery"),
    ("2", "Live Crawling"),
    ("3", "Playwright SPA Scan"),
    ("4", "Historical URL Analysis"),
    ("5", "Technology Fingerprinting"),
    ("6", "Risk Analysis"),
    ("7", "Run Full Pipeline"),
    ("8", "Export Reports"),
    ("9", "Help"),
    ("0", "Exit"),
]


def render_menu() -> str:
    lines = []

    lines.append(
        color("\nSubtrace v2 Control Panel\n", Colors.BOLD + Colors.CYAN)
    )

    for key, label in MENU_ITEMS:
        lines.append(
            f"{color(key, Colors.YELLOW)}  {label}"
        )

    return "\n".join(lines)


def print_menu() -> None:
    print(render_menu())


def get_action(choice: str) -> str:
    mapping = {k: v for k, v in MENU_ITEMS}
    return mapping.get(choice, "Invalid option")
