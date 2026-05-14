# subtrace/discovery/otx.py

from __future__ import annotations

from typing import Set

import httpx


OTX_URL = (
    "https://otx.alienvault.com"
)


async def query_otx(
    client: httpx.AsyncClient,
    domain: str,
) -> Set[str]:
    discovered = set()

    try:
        response = await client.get(
            f"{OTX_URL}/api/v1/indicators/domain/{domain}/passive_dns"
        )

        if response.status_code != 200:
            return discovered

        data = response.json()

        for row in data.get(
            "passive_dns",
            [],
        ):
            hostname = row.get(
                "hostname",
                ""
            ).lower()

            if hostname:
                discovered.add(
                    hostname
                )

    except Exception:
        pass

    return discovered
