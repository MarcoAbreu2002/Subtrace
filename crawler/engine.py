# subtrace/crawler/engine.py

from __future__ import annotations

import asyncio

from collections import deque

from typing import Dict, List, Set

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

    def __init__(
        self,
        scope,
        concurrency: int = 10,
        max_depth: int = 3,
        max_pages: int = 500,
        use_browser: bool = True,
    ):
        self.scope = scope

        self.concurrency = concurrency

        self.max_depth = max_depth

        self.max_pages = max_pages

        self.use_browser = use_browser

        self.visited: Set[str] = set()

        self.discovered: Set[str] = set()

        self.results: List[Dict] = []

        self.rate_limiter = RateLimiter()

        self.robots = RobotsCache()

        self.browser = BrowserCrawler()

        self.client = httpx.AsyncClient(
            follow_redirects=True,
            verify=False,
            timeout=20,
            headers={
                "User-Agent": "Subtrace/2.0",
            },
        )

    async def allowed(
        self,
        url: str,
    ) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https",
        ):
            return False

        if not self.scope.is_in_scope(
            parsed.hostname or ""
        ):
            return False

        return await self.robots.allowed(
            self.client,
            "Subtrace",
            url,
        )

    async def fetch(
        self,
        url: str,
    ):
        parsed = urlparse(url)

        host = parsed.hostname or ""

        await self.rate_limiter.wait(host)

        try:
            response = await self.client.get(url)

            return response

        except Exception:
            return None

    async def process_html(
        self,
        url: str,
        html: str,
        depth: int,
        queue,
    ):
        parsed = parse_html(
            html,
            url,
        )

        self.results.append({
            "type": "html",
            "url": url,
            "data": parsed,
        })

        for link in parsed["links"]:

            normalized = canonicalize(link)

            if normalized in self.visited:
                continue

            queue.append(
                (
                    normalized,
                    depth + 1,
                )
            )

        for script in parsed["scripts"]:

            if script.endswith(".js"):

                queue.append(
                    (
                        script,
                        depth + 1,
                    )
                )

    async def process_javascript(
        self,
        url: str,
        content: str,
    ):
        analysis = analyze_javascript(
            content,
            url,
        )

        self.results.append({
            "type": "javascript",
            "url": url,
            "data": analysis,
        })

        for endpoint in analysis["endpoints"]:
            self.discovered.add(endpoint)

    async def process_sourcemap(
        self,
        url: str,
        content: str,
    ):
        analysis = analyze_sourcemap(
            content
        )

        self.results.append({
            "type": "sourcemap",
            "url": url,
            "data": analysis,
        })

        for route in analysis.get(
            "routes",
            []
        ):
            self.discovered.add(route)

    async def crawl(
        self,
        seeds: List[str],
    ):
        queue = deque()

        for seed in seeds:
            queue.append(
                (
                    canonicalize(seed),
                    0,
                )
            )

        while queue:

            url, depth = queue.popleft()

            if depth > self.max_depth:
                continue

            if len(self.visited) >= self.max_pages:
                break

            if url in self.visited:
                continue

            if not await self.allowed(url):
                continue

            self.visited.add(url)

            response = await self.fetch(url)

            if not response:
                continue

            content_type = response.headers.get(
                "content-type",
                ""
            )

            text = response.text

            if "html" in content_type:

                await self.process_html(
                    url,
                    text,
                    depth,
                    queue,
                )

                if self.use_browser:

                    browser_data = await self.browser.render(
                        url
                    )

                    self.results.append({
                        "type": "browser",
                        "url": url,
                        "data": browser_data,
                    })

                    for req in browser_data["requests"]:
                        self.discovered.add(req)

            elif ".js" in url or "javascript" in content_type:

                await self.process_javascript(
                    url,
                    text,
                )

            elif url.endswith(".map"):

                await self.process_sourcemap(
                    url,
                    text,
                )

        await self.client.aclose()

        return {
            "visited": sorted(
                self.visited
            ),
            "discovered": sorted(
                self.discovered
            ),
            "results": self.results,
        }
