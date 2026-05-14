# subtrace/exporters/json_export.py

from __future__ import annotations

import json

from graph import AttackSurfaceGraph


def export_json(
    graph: AttackSurfaceGraph,
    indent: int = 2,
) -> str:
    """
    Full structured export of the attack surface graph.
    """

    return json.dumps(
        graph.to_dict(),
        indent=indent,
    )
