# subtrace/parsers/swagger.py

from __future__ import annotations

from typing import Dict

from parsers.yaml_loader import (
    load_structured_data,
)


VALID_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
}


def parse_swagger(
    content: str,
) -> Dict:
    spec = load_structured_data(
        content
    )

    if not spec:
        return {}

    if "swagger" not in spec:
        return {}

    if not str(
        spec.get(
            "swagger"
        )
    ).startswith("2"):
        return {}

    host = spec.get(
        "host",
        ""
    )

    base_path = spec.get(
        "basePath",
        ""
    )

    schemes = spec.get(
        "schemes",
        ["https"]
    )

    endpoints = []

    for path, methods in spec.get(
        "paths",
        {},
    ).items():

        for method, operation in methods.items():

            if method.lower() not in VALID_METHODS:
                continue

            operation = operation or {}

            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": operation.get(
                    "summary"
                ),
                "operation_id": operation.get(
                    "operationId"
                ),
                "parameters": operation.get(
                    "parameters",
                    [],
                ),
                "tags": operation.get(
                    "tags",
                    [],
                ),
            })

    return {
        "type": "swagger",
        "version": spec.get(
            "swagger"
        ),
        "title": (
            spec.get(
                "info",
                {}
            ).get(
                "title"
            )
        ),
        "host": host,
        "base_path": base_path,
        "schemes": schemes,
        "endpoints": endpoints,
    }
