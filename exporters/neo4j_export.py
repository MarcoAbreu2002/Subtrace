from __future__ import annotations

import json

from graph import AttackSurfaceGraph


def export_neo4j(graph: AttackSurfaceGraph) -> str:
    lines: list[str] = []

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
            f"(a {{id:'{edge.source}'}}), "
            f"(b {{id:'{edge.target}'}}) "
            f"MERGE (a)-[:{rel}]->(b);"
        )

    return "\n".join(lines)