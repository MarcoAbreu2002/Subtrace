from __future__ import annotations

from graph import AttackSurfaceGraph
from models import NodeType


def export_markdown(graph: AttackSurfaceGraph) -> str:
    lines: list[str] = []
    lines.append("# Subtrace Attack Surface Report\n")

    lines.append("## Summary\n")
    stats = graph.statistics()
    lines.append(f"- **nodes**: {stats['nodes']}")
    lines.append(f"- **edges**: {stats['edges']}")
    lines.append(f"- **types**: {stats['types']}")

    lines.append("\n---\n## Endpoints\n")

    endpoints = graph.nodes_by_type(NodeType.ENDPOINT)
    for ep in endpoints:
        m = ep.metadata or {}
        lines.append(
            f"- `{ep.value}` "
            f"**[{m.get('method','GET')}]** "
            f"Risk: `{ep.risk.value}` "
            f"Score: `{ep.score}`"
        )

    lines.append("\n---\n## Subdomains\n")
    subs = graph.nodes_by_type(NodeType.SUBDOMAIN)
    for s in subs:
        lines.append(f"- {s.value}")

    return "\n".join(lines)