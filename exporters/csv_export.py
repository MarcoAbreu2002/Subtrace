from __future__ import annotations

import csv
import io

from graph import AttackSurfaceGraph
from models import NodeType


def export_endpoints_csv(graph: AttackSurfaceGraph) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["url", "method", "risk", "score", "auth_required", "origin"])

    for node in graph.nodes_by_type(NodeType.ENDPOINT):
        m = node.metadata or {}
        writer.writerow([
            node.value,
            m.get("method", "GET"),
            node.risk.value,
            node.score,
            m.get("auth_required", False),
            m.get("origin", ""),
        ])

    return output.getvalue()