# subtrace/exporters/csv_export.py

from __future__ import annotations

import csv
import io

from graph import AttackSurfaceGraph
from models import NodeType


def export_endpoints_csv(
    graph: AttackSurfaceGraph,
) -> str:

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "url",
        "method",
        "risk",
        "score",
        "auth_required",
        "category",
        "source",
    ])

    for node in graph.nodes_of_type(
        NodeType.ENDPOINT
    ):

        m = node.metadata

        writer.writerow([
            node.value,
            m.get("method", "GET"),
            node.risk.value,
            node.score,
            m.get("auth_required", False),
            m.get("category", ""),
            node.source,
        ])

    return output.getvalue()
