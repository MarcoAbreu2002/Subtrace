# subtrace/crawler/robots.py

from __future__ import annotations

import urllib.robotparser

from typing import Dict

import httpx


class RobotsCache:

    def __init__(self):
        self.cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    async def allowed(
        self,
        client: httpx.AsyncClient,
        user_agent: str,
        url: str,
    ) -> bool:
        parsed = httpx.URL(url)

        host = parsed.host

        if not host:
            return False

        if host not in self.cache:

            robots_url = f"{parsed.scheme}://{host}/robots.txt"

            parser = urllib.robotparser.RobotFileParser()

            try:
                response = await client.get(
                    robots_url
                )

                parser.parse(
                    response.text.splitlines()
                )

            except Exception:
                parser = urllib.robotparser.RobotFileParser()

            self.cache[host] = parser

        parser = self.cache[host]

        return parser.can_fetch(
            user_agent,
            url,
        )
