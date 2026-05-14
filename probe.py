# probe.py
from __future__ import annotations

import asyncio
from typing import Dict, List
import httpx


async def _probe_one(client: httpx.AsyncClient, url: str) -> Dict:
    try:
        r = await client.get(url)
        return {
            "url": url,
            "ok": True,
            "status_code": r.status_code,
            "final_url": str(r.url),
            "content_type": r.headers.get("content-type", ""),
            "server": r.headers.get("server", ""),
        }
    except Exception as e:
        return {
            "url": url,
            "ok": False,
            "error": str(e),
        }


async def probe_hosts(
    hosts: List[str],
    concurrency: int = 50,
    timeout: int = 10,
) -> List[Dict]:
    """
    For each host probes both https://host and http://host.
    Returns one record per (scheme,host).
    """
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        verify=False,
        headers={"User-Agent": "Subtrace/2.0"},
    ) as client:

        async def run(url: str):
            async with sem:
                return await _probe_one(client, url)

        tasks = []
        for h in hosts:
            h = h.strip()
            if not h:
                continue
            tasks.append(run(f"https://{h}"))
            tasks.append(run(f"http://{h}"))

        return await asyncio.gather(*tasks)
