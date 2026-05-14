# subtrace/parsers/openapi.py

from __future__ import annotations

from typing import Dict, List

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


def parse_openapi(
    content: str,
) -> Dict:
    spec = load_structured_data(
        content
    )

    if not spec:
        return {}

    if "openapi" not in spec:
        return {}

    servers = []

    for server in spec.get(
        "servers",
        [],
    ):
        url = server.get(
            "url",
            ""
        )

        if url:
            servers.append(url)

    endpoints = []

    paths = spec.get(
        "paths",
        {}
    )

    for path, methods in paths.items():

        if not isinstance(
            methods,
            dict,
        ):
            continue

        for method, operation in methods.items():

            if method.lower() not in VALID_METHODS:
                continue

            operation = operation or {}

            parameters = []

            for parameter in operation.get(
                "parameters",
                [],
            ):
                parameters.append({
                    "name": parameter.get(
                        "name"
                    ),
                    "in": parameter.get(
                        "in"
                    ),
                    "required": parameter.get(
                        "required",
                        False,
                    ),
                    "schema": parameter.get(
                        "schema",
                        {},
                    ),
                })

            endpoints.append({
                "path": path,
                "method": method.upper(),
                "summary": operation.get(
                    "summary"
                ),
                "operation_id": operation.get(
                    "operationId"
                ),
                "tags": operation.get(
                    "tags",
                    [],
                ),
                "parameters": parameters,
                "security": operation.get(
                    "security",
                    [],
                ),
            })

    security_schemes = (
        spec.get(
            "components",
            {}
        )
        .get(
            "securitySchemes",
            {}
        )
    )

    return {
        "type": "openapi",
        "version": spec.get(
            "openapi"
        ),
        "title": (
            spec.get(
                "info",
                {}
            ).get(
                "title"
            )
        ),
        "servers": servers,
        "endpoints": endpoints,
        "security_schemes": security_schemes,
    }
