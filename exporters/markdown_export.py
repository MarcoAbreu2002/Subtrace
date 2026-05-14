# subtrace/exporters/markdown_export.py

from __future__ import annotations

from graph import AttackSurfaceGraph
from models import NodeType


def export_markdown(
    graph: AttackSurfaceGraph,
) -> str:

    lines = []

    lines.append("# Subtrace Attack Surface Report\n")

    lines.append("## Summary\n")

    stats = graph.stats()

    for k, v in stats.items():
        lines.append(f"- **{k}**: {v}")

    lines.append("\n---\n")
    lines.append("## Endpoints\n")

    endpoints = graph.nodes_of_type(
        NodeType.ENDPOINT
    )

    for ep in endpoints:

        m = ep.metadata

        lines.append(
            f"- `{ep.value}` "
            f"**[{m.get('method','GET')}]** "
            f"Risk: `{ep.risk.value}` "
            f"Score: `{ep.score}`"
        )

    lines.append("\n---\n")
    lines.append("## Subdomains\n")

    subs = graph.nodes_of_type(
        NodeType.SUBDOMAIN
    )

    for s in subs:
        lines.append(f"- {s.value}")

    return "\n".join(lines)
