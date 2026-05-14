# subtrace/parsers/graphql.py

from __future__ import annotations

from typing import Dict, List


INTROSPECTION_KEYS = {
    "__schema",
    "__type",
    "queryType",
    "mutationType",
}


def looks_like_graphql(
    content: str,
) -> bool:
    lower = content.lower()

    return (
        "graphql" in lower
        or "__schema" in lower
        or "querytype" in lower
    )


def parse_introspection(
    data: Dict,
) -> Dict:
    schema = (
        data.get("data", {})
        .get("__schema", {})
    )

    types = schema.get(
        "types",
        []
    )

    queries = []

    mutations = []

    subscriptions = []

    type_names = []

    for item in types:

        name = item.get(
            "name"
        )

        if not name:
            continue

        type_names.append(name)

        fields = item.get(
            "fields",
            []
        )

        if name == "Query":

            for field in fields:
                queries.append(
                    field.get("name")
                )

        elif name == "Mutation":

            for field in fields:
                mutations.append(
                    field.get("name")
                )

        elif name == "Subscription":

            for field in fields:
                subscriptions.append(
                    field.get("name")
                )

    return {
        "queries": sorted(
            q for q in queries if q
        ),
        "mutations": sorted(
            m for m in mutations if m
        ),
        "subscriptions": sorted(
            s for s in subscriptions if s
        ),
        "types": sorted(
            type_names
        ),
    }


def parse_graphql_response(
    content,
) -> Dict:
    if isinstance(
        content,
        str,
    ):
        return {
            "graphql_detected": looks_like_graphql(
                content
            ),
        }

    if isinstance(
        content,
        dict,
    ):
        parsed = parse_introspection(
            content
        )

        parsed[
            "graphql_detected"
        ] = True

        return parsed

    return {}
