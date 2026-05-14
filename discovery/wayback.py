# subtrace/discovery/wayback.py

from __future__ import annotations

from typing import Dict, List, Set

import httpx


WAYBACK_URL = (
    "http://web.archive.org/cdx/search/cdx"
)


async def query_wayback(
    client: httpx.AsyncClient,
    domain: str,
) -> Dict:
    subdomains = set()

    urls = set()

    try:
        response = await client.get(
            WAYBACK_URL,
            params={
                "url": f"*.{domain}/*",
                "output": "json",
                "fl": "original",
                "collapse": "urlkey",
                "limit": "100000",
            },
        )

        if response.status_code != 200:
            return {
                "subdomains": [],
                "urls": [],
            }

        data = response.json()

        for row in data[1:]:

            try:
                original = row[0]

            except Exception:
                continue

            urls.add(original)

            try:
                parsed = httpx.URL(original)

                if parsed.host:
                    subdomains.add(
                        parsed.host.lower()
                    )

            except Exception:
                continue

    except Exception:
        pass

    return {
        "subdomains": sorted(
            subdomains
        ),
        "urls": sorted(
            urls
        ),
    }
