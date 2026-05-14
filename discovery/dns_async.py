# subtrace/discovery/dns_async.py

from __future__ import annotations

import asyncio
import socket

from typing import Dict, List

import aiodns


class AsyncDNSResolver:

    def __init__(
        self,
        concurrency: int = 100,
    ):
        self.resolver = aiodns.DNSResolver()

        self.semaphore = asyncio.Semaphore(concurrency)

        self.cache: Dict[str, Dict] = {}

    async def resolve(
        self,
        hostname: str,
    ) -> Dict:
        hostname = hostname.lower().strip()

        if hostname in self.cache:
            return self.cache[hostname]

        async with self.semaphore:

            result = {
                "hostname": hostname,
                "ips": [],
                "cname": None,
            }

            try:
                response = await self.resolver.gethostbyname(
                    hostname,
                    socket.AF_INET,
                )

                result["ips"] = response.addresses

            except Exception:
                pass

            try:
                cname = await self.resolver.query(
                    hostname,
                    "CNAME",
                )

                if cname:
                    result["cname"] = cname[0].host

            except Exception:
                pass

            self.cache[hostname] = result

            return result

    async def resolve_many(
        self,
        hosts: List[str],
    ) -> List[Dict]:
        tasks = [
            self.resolve(host)
            for host in hosts
        ]

        return await asyncio.gather(*tasks)
