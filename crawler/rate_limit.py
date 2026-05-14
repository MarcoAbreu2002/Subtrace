# subtrace/crawler/rate_limit.py

from __future__ import annotations

import asyncio
import time

from collections import defaultdict


class RateLimiter:

    def __init__(
        self,
        requests_per_second: float = 2.0,
    ):
        self.interval = 1.0 / requests_per_second

        self.host_times = defaultdict(float)

        self.lock = asyncio.Lock()

    async def wait(
        self,
        host: str,
    ):
        async with self.lock:

            now = time.monotonic()

            last = self.host_times[host]

            delta = now - last

            if delta < self.interval:
                await asyncio.sleep(
                    self.interval - delta
                )

            self.host_times[host] = time.monotonic()
