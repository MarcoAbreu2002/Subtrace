# subtrace/exporters/html_export.py

from __future__ import annotations

from graph import AttackSurfaceGraph
from models import NodeType


def export_html(
    graph: AttackSurfaceGraph,
) -> str:

    endpoints = graph.nodes_of_type(
        NodeType.ENDPOINT
    )

    html = [
        "<html>",
        "<head><title>Subtrace Report</title></head>",
        "<body>",
        "<h1>Subtrace Attack Surface Report</h1>",
        "<h2>Endpoints</h2>",
        "<ul>",
    ]

    for ep in endpoints:

        m = ep.metadata

        html.append(
            "<li>"
            f"<b>{ep.value}</b> "
            f"[{m.get('method','GET')}] "
            f"Risk: {ep.risk.value} "
            f"Score: {ep.score}"
            "</li>"
        )

    html += [
        "</ul>",
        "</body>",
        "</html>",
    ]

    return "\n".join(html)
