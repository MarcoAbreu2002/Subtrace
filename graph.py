# subtrace/graph.py

from __future__ import annotations

import json

from collections import defaultdict
from typing import Dict, List, Optional

import networkx as nx

from models import (
    Edge,
    EdgeType,
    Node,
    NodeType,
)


class AttackSurfaceGraph:

    def __init__(self):
        self.graph = nx.MultiDiGraph()

        self.node_index: Dict[str, str] = {}

    # ---------------------------------------------------------
    # NODES
    # ---------------------------------------------------------

    def _make_key(
        self,
        node_type: NodeType,
        value: str,
    ) -> str:
        return f"{node_type.value}:{value.strip().lower()}"

    def add_node(self, node: Node) -> str:
        key = self._make_key(node.type, node.value)

        if key in self.node_index:
            existing_id = self.node_index[key]

            existing = self.graph.nodes[existing_id]["data"]

            existing.confidence = max(
                existing.confidence,
                node.confidence,
            )

            existing.tags = list(
                set(existing.tags + node.tags)
            )

            existing.metadata.update(node.metadata)

            return existing_id

        self.graph.add_node(
            node.id,
            data=node,
        )

        self.node_index[key] = node.id

        return node.id

    def get_node(self, node_id: str) -> Optional[Node]:
        if node_id not in self.graph:
            return None

        return self.graph.nodes[node_id]["data"]

    def find(
        self,
        node_type: NodeType,
        value: str,
    ) -> Optional[Node]:
        key = self._make_key(node_type, value)

        node_id = self.node_index.get(key)

        if not node_id:
            return None

        return self.get_node(node_id)

    def all_nodes(self) -> List[Node]:
        return [
            data["data"]
            for _, data in self.graph.nodes(data=True)
        ]

    # ---------------------------------------------------------
    # EDGES
    # ---------------------------------------------------------

    def add_edge(self, edge: Edge):
        if edge.source not in self.graph:
            return

        if edge.target not in self.graph:
            return

        self.graph.add_edge(
            edge.source,
            edge.target,
            key=edge.id,
            data=edge,
        )

    def connect(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
    ):
        edge = Edge(
            source=source_id,
            target=target_id,
            type=edge_type,
        )

        self.add_edge(edge)

    def all_edges(self) -> List[Edge]:
        return [
            data["data"]
            for _, _, data in self.graph.edges(data=True)
        ]

    # ---------------------------------------------------------
    # ANALYTICS
    # ---------------------------------------------------------

    def nodes_by_type(
        self,
        node_type: NodeType,
    ) -> List[Node]:
        return [
            n
            for n in self.all_nodes()
            if n.type == node_type
        ]

    def degree_rank(
        self,
        limit: int = 20,
    ):
        ranking = []

        for node_id in self.graph.nodes:
            degree = self.graph.degree(node_id)

            node = self.get_node(node_id)

            ranking.append((degree, node))

        ranking.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return ranking[:limit]

    def attack_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 5,
    ):
        try:
            return list(
                nx.all_simple_paths(
                    self.graph,
                    source,
                    target,
                    cutoff=max_depth,
                )
            )

        except Exception:
            return []

    def connected_assets(
        self,
        node_id: str,
    ) -> List[Node]:
        related = []

        for neighbor in self.graph.neighbors(node_id):
            node = self.get_node(neighbor)

            if node:
                related.append(node)

        return related

    def statistics(self):
        stats = defaultdict(int)

        for node in self.all_nodes():
            stats[node.type.value] += 1

        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "types": dict(stats),
        }

    # ---------------------------------------------------------
    # EXPORTS
    # ---------------------------------------------------------

    def to_dict(self):
        return {
            "nodes": [
                n.to_dict()
                for n in self.all_nodes()
            ],
            "edges": [
                e.to_dict()
                for e in self.all_edges()
            ],
            "statistics": self.statistics(),
        }

    def to_json(
        self,
        indent: int = 2,
    ):
        return json.dumps(
            self.to_dict(),
            indent=indent,
        )
