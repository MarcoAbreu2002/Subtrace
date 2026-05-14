# crawler/engine.py

from __future__ import annotations

import asyncio
from collections import deque
from typing import Callable, Dict, List, Optional, Set
from urllib.parse import urlparse

import httpx

from crawler.browser import BrowserCrawler
from crawler.canonicalize import canonicalize
from crawler.extractor_html import parse_html
from crawler.extractor_js import analyze_javascript
from crawler.extractor_sourcemap import analyze_sourcemap
from crawler.rate_limit import RateLimiter
from crawler.robots import RobotsCache


class CrawlEngine:
    """
    Async crawler. Still single-worker (sequential) by design for now,
    but provides live progress callbacks so the CLI can show activity.
    """

    def __init__(
        self,
        scope,
        concurrency: int = 10,
        max_depth: int = 3,
        max_pages: int = 500,
        use_browser: bool = True,
        on_update: Optional[Callable[[Dict], None]] = None,
        log_every: int = 5,
    ):
        self.scope = scope

        self.concurrency = concurrency  # not yet used (future worker pool)
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.use_browser = use_browser

        self.visited: Set[str] = set()
        self.discovered: Set[str] = set()
        self.results: List[Dict] = []

        self.rate_limiter = RateLimiter()
        self.robots = RobotsCache()
        self.browser = BrowserCrawler()

        self.on_update = on_update
        self.log_every = max(1, log_every)
        self._tick = 0
        self._queue_size = 0
        self._current_depth = 0

        self.client = httpx.AsyncClient(
            follow_redirects=True,
            verify=False,
            timeout=20,
            headers={"User-Agent": "Subtrace/2.0"},
        )

    def _emit_update(self, current_url: str = "") -> None:
        if not self.on_update:
            return

        self.on_update(
            {
                "current_url": current_url,
                "visited": len(self.visited),
                "discovered": len(self.discovered),
                "results": len(self.results),
                "queue_size": self._queue_size,
                "depth": self._current_depth,
                "max_pages": self.max_pages,
            }
        )

    async def allowed(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if not self.scope.is_in_scope(parsed.hostname or ""):
            return False

        # obey robots by default (your RobotsCache does this)
        return await self.robots.allowed(self.client, "Subtrace", url)

    async def fetch(self, url: str):
        parsed = urlparse(url)
        host = parsed.hostname or ""

        await self.rate_limiter.wait(host)

        try:
            response = await self.client.get(url)
            return response
        except Exception:
            return None

    async def process_html(self, url: str, html: str, depth: int, queue: deque):
        parsed = parse_html(html, url)

        self.results.append({"type": "html", "url": url, "data": parsed})

        for link in parsed["links"]:
            normalized = canonicalize(link)
            if normalized in self.visited:
                continue
            queue.append((normalized, depth + 1))

        for script in parsed["scripts"]:
            if script.endswith(".js"):
                queue.append((script, depth + 1))

    async def process_javascript(self, url: str, content: str):
        analysis = analyze_javascript(content, url)

        self.results.append({"type": "javascript", "url": url, "data": analysis})

        for endpoint in analysis.get("endpoints", []):
            self.discovered.add(endpoint)

    async def process_sourcemap(self, url: str, content: str):
        analysis = analyze_sourcemap(content)

        self.results.append({"type": "sourcemap", "url": url, "data": analysis})

        for route in analysis.get("routes", []):
            self.discovered.add(route)

    async def crawl(self, seeds: List[str]):
        queue: deque = deque()

        for seed in seeds:
            queue.append((canonicalize(seed), 0))

        self._queue_size = len(queue)
        self._emit_update(current_url="starting")

        while queue:
            url, depth = queue.popleft()

            self._queue_size = len(queue)
            self._current_depth = depth

            if depth > self.max_depth:
                continue

            if len(self.visited) >= self.max_pages:
                break

            if url in self.visited:
                continue

            if not await self.allowed(url):
                continue

            self.visited.add(url)

            # progress update
            self._tick += 1
            if self._tick % self.log_every == 0:
                self._emit_update(current_url=url)

            response = await self.fetch(url)
            if not response:
                continue

            content_type = response.headers.get("content-type", "")
            text = response.text

            # store minimal response metadata (useful for reports)
            self.results.append(
                {
                    "type": "response",
                    "url": url,
                    "data": {
                        "status_code": response.status_code,
                        "content_type": content_type,
                        "response_size": len(response.content or b""),
                        # keep headers small-ish (you can expand later)
                        "headers": {
                            k: v
                            for k, v in response.headers.items()
                            if k.lower()
                            in (
                                "server",
                                "content-type",
                                "set-cookie",
                                "location",
                                "x-powered-by",
                                "cf-ray",
                                "via",
                            )
                        },
                    },
                }
            )

            if "html" in content_type:
                await self.process_html(url, text, depth, queue)

                if self.use_browser:
                    browser_data = await self.browser.render(url)

                    self.results.append(
                        {"type": "browser", "url": url, "data": browser_data}
                    )

                    for req in browser_data.get("requests", []):
                        self.discovered.add(req)

            elif url.endswith(".map"):
                await self.process_sourcemap(url, text)

            elif ".js" in url or "javascript" in content_type:
                await self.process_javascript(url, text)

        self._emit_update(current_url="done")

        await self.client.aclose()

        return {
            "visited": sorted(self.visited),
            "discovered": sorted(self.discovered),
            "results": self.results,
        }