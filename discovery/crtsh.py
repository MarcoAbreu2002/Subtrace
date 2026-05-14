# subtrace/discovery/crtsh.py

from __future__ import annotations

from typing import Set

import httpx


CRT_ENDPOINT = (
    "https://crt.sh/"
)


async def query_crtsh(
    client: httpx.AsyncClient,
    domain: str,
) -> Set[str]:
    discovered = set()

    try:
        response = await client.get(
            CRT_ENDPOINT,
            params={
                "q": f"%.{domain}",
                "output": "json",
            },
        )

        if response.status_code != 200:
            return discovered

        try:
            data = response.json()

        except Exception:
            return discovered

        for row in data:

            value = row.get(
                "name_value",
                "",
            )

            for item in value.split("\n"):

                item = item.strip().lower()

                if not item:
                    continue

                if item.startswith("*."):
                    item = item[2:]

                discovered.add(item)

    except Exception:
        pass

    return discovered
