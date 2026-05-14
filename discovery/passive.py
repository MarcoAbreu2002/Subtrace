# subtrace/discovery/passive.py

from __future__ import annotations

import asyncio

from typing import Dict, Set

import httpx

from discovery.crtsh import query_crtsh
from discovery.dns_async import AsyncDNSResolver
from discovery.hackertarget import (
    query_hackertarget,
)
from discovery.otx import query_otx
from discovery.wayback import (
    query_wayback,
)


class PassiveDiscovery:

    def __init__(
        self,
        timeout: int = 20,
    ):
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Subtrace/2.0",
            },
        )

        self.resolver = AsyncDNSResolver()

    async def enumerate(
        self,
        domain: str,
    ) -> Dict:
        tasks = [
            query_crtsh(
                self.client,
                domain,
            ),
            query_otx(
                self.client,
                domain,
            ),
            query_hackertarget(
                self.client,
                domain,
            ),
            query_wayback(
                self.client,
                domain,
            ),
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        all_subdomains: Set[str] = set()

        historical_urls = set()

        for result in results:

            if isinstance(
                result,
                Exception,
            ):
                continue

            if isinstance(
                result,
                dict,
            ):
                all_subdomains.update(
                    result.get(
                        "subdomains",
                        []
                    )
                )

                historical_urls.update(
                    result.get(
                        "urls",
                        []
                    )
                )

            elif isinstance(
                result,
                set,
            ):
                all_subdomains.update(
                    result
                )

        resolved = await self.resolver.resolve_many(
            sorted(all_subdomains)
        )

        return {
            "subdomains": sorted(
                all_subdomains
            ),
            "historical_urls": sorted(
                historical_urls
            ),
            "resolved": resolved,
        }

    async def close(
        self,
    ):
        await self.client.aclose()
