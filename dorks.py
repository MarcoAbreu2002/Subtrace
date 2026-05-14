# dorks.py
from __future__ import annotations

from urllib.parse import quote_plus

DEFAULT_DORKS = [
    ('Sensitive files', 'ext:env OR ext:sql OR ext:bak OR ext:old OR ext:backup OR ext:log'),
    ('Directory listings', '"index of /"'),
    ('Config files', 'ext:yaml OR ext:yml OR ext:json (config OR settings OR secrets)'),
    ('Cloud/storage', '(s3 OR "amazonaws.com" OR "storage.googleapis.com" OR "blob.core.windows.net")'),
    ('JWT / tokens', '"eyJ" "Bearer "'),
    ('API docs', '("swagger" OR "openapi" OR "api-docs" OR "swagger-ui")'),
    ('GraphQL', 'graphql OR "GraphiQL" OR "graphql/playground"'),
    ('Login panels', 'inurl:login OR inurl:signin OR inurl:admin'),
    ('Debug', 'inurl:debug OR inurl:test OR inurl:staging OR inurl:dev'),
    ('Backups', '("backup" OR "dump") (ext:zip OR ext:tar OR ext:gz)'),
]

def build_dorks(domain: str, extra: list[tuple[str, str]] | None = None) -> list[dict]:
    """
    Returns list of {name, query, url}.
    Does not call Google. Just generates queries/links.
    """
    domain = domain.strip().lower()
    items = DEFAULT_DORKS + (extra or [])

    out = []
    for name, q in items:
        query = f"site:{domain} {q}"
        url = f"https://www.google.com/search?q={quote_plus(query)}"
        out.append({"name": name, "query": query, "url": url})
    return out
