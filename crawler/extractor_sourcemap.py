# subtrace/crawler/extractor_sourcemap.py

from __future__ import annotations

import json
import re

from typing import Dict, List, Set


ROUTE_RE = re.compile(
    r"/[A-Za-z0-9_\-/]{3,}"
)


def parse_source_map(
    content: str,
) -> Dict:
    try:
        data = json.loads(content)

    except Exception:
        return {}

    return {
        "version": data.get("version"),
        "sources": data.get("sources", []),
        "names": data.get("names", []),
        "mappings": data.get("mappings"),
    }


def extract_routes_from_sources(
    sources: List[str],
) -> Set[str]:
    found = set()

    for source in sources:

        for match in ROUTE_RE.findall(source):

            if len(match) < 4:
                continue

            found.add(match)

    return found


def analyze_sourcemap(
    content: str,
) -> Dict:
    parsed = parse_source_map(content)

    if not parsed:
        return {}

    routes = extract_routes_from_sources(
        parsed.get("sources", [])
    )

    return {
        "sources": parsed.get("sources", []),
        "routes": sorted(routes),
        "names_count": len(
            parsed.get("names", [])
        ),
    }
