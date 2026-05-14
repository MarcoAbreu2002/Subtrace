# subtrace/exporters/neo4j_export.py

from __future__ import annotations

import json

from graph import AttackSurfaceGraph
from models import NodeType


def export_neo4j(
    graph: AttackSurfaceGraph,
) -> str:

    lines = []

    for node in graph.all_nodes():

        label = node.type.value.upper()

        props = json.dumps({
            "id": node.id,
            "value": node.value,
            "risk": node.risk.value,
            "score": node.score,
        })

        lines.append(
            f"MERGE (n:{label} {{id: '{node.id}'}}) "
            f"SET n += {props};"
        )

    for edge in graph.all_edges():

        rel = edge.type.value.upper()

        lines.append(
            "MATCH "
            f"(a {{id:'{edge.source_id}'}}), "
            f"(b {{id:'{edge.target_id}'}}) "
            f"MERGE (a)-[:{rel}]->(b);"
        )

    return "\n".join(lines)
