# subtrace/storage.py

from __future__ import annotations

import json

import aiosqlite

from models import Node, Edge


CREATE_NODES = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    type TEXT,
    value TEXT,
    label TEXT,
    risk TEXT,
    score REAL,
    confidence REAL,
    metadata TEXT,
    tags TEXT,
    discovered_at TEXT
)
"""


CREATE_EDGES = """
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source TEXT,
    target TEXT,
    type TEXT,
    confidence REAL,
    metadata TEXT
)
"""


CREATE_SCAN = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT,
    started_at TEXT,
    completed_at TEXT,
    metadata TEXT
)
"""


class Storage:

    def __init__(
        self,
        db_path: str = "subtrace.db",
    ):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_NODES)

            await db.execute(CREATE_EDGES)

            await db.execute(CREATE_SCAN)

            await db.commit()

    # ---------------------------------------------------------
    # INSERTS
    # ---------------------------------------------------------

    async def insert_node(
        self,
        node: Node,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO nodes (
                    id,
                    type,
                    value,
                    label,
                    risk,
                    score,
                    confidence,
                    metadata,
                    tags,
                    discovered_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.id,
                    node.type.value,
                    node.value,
                    node.label,
                    node.risk.value,
                    node.score,
                    node.confidence,
                    json.dumps(node.metadata),
                    json.dumps(node.tags),
                    node.discovered_at,
                ),
            )

            await db.commit()

    async def insert_edge(
        self,
        edge: Edge,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO edges (
                    id,
                    source,
                    target,
                    type,
                    confidence,
                    metadata
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    edge.id,
                    edge.source,
                    edge.target,
                    edge.type.value,
                    edge.confidence,
                    json.dumps(edge.metadata),
                ),
            )

            await db.commit()

    # ---------------------------------------------------------
    # QUERIES
    # ---------------------------------------------------------

    async def fetch_nodes(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM nodes"
            )

            return await cursor.fetchall()

    async def fetch_edges(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM edges"
            )

            return await cursor.fetchall()

    async def stats(self):
        async with aiosqlite.connect(self.db_path) as db:

            node_count = await db.execute_fetchall(
                "SELECT COUNT(*) FROM nodes"
            )

            edge_count = await db.execute_fetchall(
                "SELECT COUNT(*) FROM edges"
            )

            return {
                "nodes": node_count[0][0],
                "edges": edge_count[0][0],
            }
