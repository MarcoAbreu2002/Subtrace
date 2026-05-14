# subtrace/discovery/hackertarget.py

from __future__ import annotations

from typing import Set

import httpx


API_URL = (
    "https://api.hackertarget.com/hostsearch/"
)


async def query_hackertarget(
    client: httpx.AsyncClient,
    domain: str,
) -> Set[str]:
    discovered = set()

    try:
        response = await client.get(
            API_URL,
            params={
                "q": domain,
            },
        )

        if response.status_code != 200:
            return discovered

        text = response.text

        if "error" in text.lower():
            return discovered

        for line in text.splitlines():

            try:
                hostname = (
                    line.split(",")[0]
                    .strip()
                    .lower()
                )

            except Exception:
                continue

            if hostname:
                discovered.add(
                    hostname
                )

    except Exception:
        pass

    return discovered
