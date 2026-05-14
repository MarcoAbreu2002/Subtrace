# subtrace/crawler/canonicalize.py

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlparse,
)


TRACKING_PARAMS = {
    "utm_source",
    "utm_campaign",
    "utm_medium",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}


def canonicalize(
    url: str,
) -> str:
    parsed = urlparse(url)

    query = parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )

    filtered = []

    seen = set()

    for key, value in sorted(query):

        if key in TRACKING_PARAMS:
            continue

        token = (key, value)

        if token in seen:
            continue

        seen.add(token)

        filtered.append((key, value))

    normalized = parsed._replace(
        fragment="",
        query=urlencode(filtered),
    )

    result = normalized.geturl()

    if result.endswith("/"):
        result = result[:-1]

    return result
