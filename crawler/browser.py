# subtrace/crawler/browser.py

from __future__ import annotations

import asyncio

from typing import Dict, List, Set

from playwright.async_api import (
    async_playwright,
)


class BrowserCrawler:

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
    ):
        self.headless = headless
        self.timeout = timeout

    async def render(
        self,
        url: str,
    ) -> Dict:
        requests: Set[str] = set()

        responses: Set[str] = set()

        console_logs: List[str] = []

        async with async_playwright() as p:

            browser = await p.chromium.launch(
                headless=self.headless,
            )

            page = await browser.new_page()

            page.set_default_timeout(
                self.timeout
            )

            page.on(
                "request",
                lambda r: requests.add(r.url),
            )

            page.on(
                "response",
                lambda r: responses.add(r.url),
            )

            page.on(
                "console",
                lambda msg: console_logs.append(
                    msg.text
                ),
            )

            try:
                await page.goto(
                    url,
                    wait_until="networkidle",
                )

                html = await page.content()

                title = await page.title()

                cookies = await page.context.cookies()

                local_storage = await page.evaluate(
                    "() => Object.assign({}, window.localStorage)"
                )

                session_storage = await page.evaluate(
                    "() => Object.assign({}, window.sessionStorage)"
                )

            except Exception:
                html = ""
                title = ""
                cookies = []
                local_storage = {}
                session_storage = {}

            await browser.close()

        return {
            "html": html,
            "title": title,
            "requests": sorted(requests),
            "responses": sorted(responses),
            "cookies": cookies,
            "local_storage": local_storage,
            "session_storage": session_storage,
            "console": console_logs,
        }
