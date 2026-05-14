# subtrace/relationships.py

from __future__ import annotations

import re

from models import NodeType, Edge, EdgeType


API_PREFIX = re.compile(r"/api/|/v\d+/", re.I)
AUTH_PATHS = re.compile(r"/auth|/login|/token", re.I)
UPLOAD_PATHS = re.compile(r"/upload|/file|/media", re.I)
ADMIN_PATHS = re.compile(r"/admin|/dashboard|/console", re.I)


def infer_relationships(graph) -> None:
    """
    Builds edges between discovered nodes.
    """

    nodes = graph.all_nodes()

    # ─────────────────────────────────────────────
    # Endpoint → Endpoint relationships
    # ─────────────────────────────────────────────
    for a in nodes:
        if a.type.value != "endpoint":
            continue

        for b in nodes:
            if a.id == b.id:
                continue

            if b.type.value != "endpoint":
                continue

            # Same host grouping → weak linkage
            if _same_base(a.value, b.value):
                graph.add_edge(Edge(
                    source_id=a.id,
                    target_id=b.id,
                    type=EdgeType.LINKS_TO,
                    confidence=0.3,
                ))

    # ─────────────────────────────────────────────
    # Endpoint → Subdomain mapping
    # ─────────────────────────────────────────────
    for ep in nodes:
        if ep.type.value != "endpoint":
            continue

        for sub in nodes:
            if sub.type.value not in ("domain", "subdomain"):
                continue

            if sub.value in ep.value:
                graph.add_edge(Edge(
                    source_id=sub.id,
                    target_id=ep.id,
                    type=EdgeType.SERVES,
                    confidence=0.8,
                ))

    # ─────────────────────────────────────────────
    # Auth relationships
    # ─────────────────────────────────────────────
    for ep in nodes:
        if ep.type.value != "endpoint":
            continue

        if AUTH_PATHS.search(ep.value):
            graph.add_edge(Edge(
                source_id=ep.id,
                target_id=ep.id,
                type=EdgeType.REQUIRES_AUTH,
                confidence=0.9,
            ))

    # ─────────────────────────────────────────────
    # Upload / sensitive surfaces
    # ─────────────────────────────────────────────
    for ep in nodes:
        if ep.type.value != "endpoint":
            continue

        if UPLOAD_PATHS.search(ep.value):
            ep.metadata["attack_surface"] = "upload"
            ep.score += 10

        if ADMIN_PATHS.search(ep.value):
            ep.metadata["attack_surface"] = "admin"
            ep.score += 20

    # ─────────────────────────────────────────────
    # API structure inference
    # ─────────────────────────────────────────────
    for ep in nodes:
        if ep.type.value != "endpoint":
            continue

        if API_PREFIX.search(ep.value):
            ep.metadata["api_type"] = "rest"

            graph.add_edge(Edge(
                source_id=ep.id,
                target_id=ep.id,
                type=EdgeType.BELONGS_TO,
                confidence=0.6,
            ))


def _same_base(url_a: str, url_b: str) -> bool:
    """
    Very lightweight grouping heuristic:
    same path depth up to first segment difference.
    """

    try:
        a_parts = url_a.split("/")
        b_parts = url_b.split("/")

        return a_parts[2] == b_parts[2]

    except Exception:
        return False
