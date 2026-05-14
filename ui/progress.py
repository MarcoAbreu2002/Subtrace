# subtrace/ui/progress.py

from __future__ import annotations

import time
import sys

from ui.colors import Colors, color


class Progress:
    def __init__(self):
        self.start_time = time.time()

    def log(self, message: str, level: str = "info") -> None:

        prefix_map = {
            "info": color("[*]", Colors.BLUE),
            "ok": color("[+]", Colors.GREEN),
            "warn": color("[!]", Colors.YELLOW),
            "error": color("[-]", Colors.RED),
        }

        prefix = prefix_map.get(level, "[*]")

        elapsed = f"{time.time() - self.start_time:.2f}s"

        sys.stdout.write(
            f"{prefix} {message} ({elapsed})\n"
        )
        sys.stdout.flush()

    def reset_timer(self) -> None:
        self.start_time = time.time()
