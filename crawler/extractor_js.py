# subtrace/crawler/extractor_js.py

from __future__ import annotations

import re

from typing import Dict, List, Set

from urllib.parse import urlparse

import esprima


FETCH_RE = re.compile(
    r"""(?:fetch|axios\.(?:get|post|put|delete|patch)|\.ajax)\s*\(\s*['"`]([^'"`]+)""",
    re.I,
)

URL_RE = re.compile(
    r"""['"`](https?://[^'"`\s]+|/[^'"`\s]+)['"`]""",
    re.I,
)

GRAPHQL_RE = re.compile(
    r"(query|mutation|subscription)\s+",
    re.I,
)

JWT_RE = re.compile(
    r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
)

WS_RE = re.compile(
    r"""wss?://[^'"`\s]+""",
    re.I,
)


def normalize_js_endpoint(
    value: str,
    base_url: str,
) -> str:
    if value.startswith("http"):
        return value

    parsed = urlparse(base_url)

    return f"{parsed.scheme}://{parsed.netloc}{value}"


def extract_regex_endpoints(
    content: str,
    base_url: str,
) -> Set[str]:
    discovered = set()

    for pattern in [FETCH_RE, URL_RE]:

        for match in pattern.finditer(content):

            value = match.group(1).strip()

            if len(value) < 2:
                continue

            if value.startswith("//"):
                continue

            endpoint = normalize_js_endpoint(
                value,
                base_url,
            )

            discovered.add(endpoint)

    return discovered


def extract_graphql(
    content: str,
) -> bool:
    return bool(
        GRAPHQL_RE.search(content)
    )


def extract_tokens(
    content: str,
) -> List[str]:
    return JWT_RE.findall(content)


def extract_websockets(
    content: str,
) -> List[str]:
    return WS_RE.findall(content)


def ast_extract_routes(
    content: str,
    base_url: str,
) -> Set[str]:
    routes = set()

    try:
        tree = esprima.parseScript(
            content,
            tolerant=True,
        )

    except Exception:
        return routes

    stack = [tree]

    while stack:

        node = stack.pop()

        if isinstance(node, list):
            stack.extend(node)
            continue

        if not hasattr(node, "__dict__"):
            continue

        props = vars(node)

        if getattr(node, "type", None) == "Literal":

            value = getattr(node, "value", None)

            if isinstance(value, str):

                if value.startswith("/"):
                    routes.add(
                        normalize_js_endpoint(
                            value,
                            base_url,
                        )
                    )

        for value in props.values():

            if isinstance(value, list):
                stack.extend(value)

            elif hasattr(value, "__dict__"):
                stack.append(value)

    return routes


def analyze_javascript(
    content: str,
    base_url: str,
) -> Dict:
    regex_routes = extract_regex_endpoints(
        content,
        base_url,
    )

    ast_routes = ast_extract_routes(
        content,
        base_url,
    )

    return {
        "endpoints": sorted(
            regex_routes | ast_routes
        ),
        "graphql": extract_graphql(content),
        "tokens": extract_tokens(content),
        "websockets": extract_websockets(content),
    }
