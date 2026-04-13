#!/usr/bin/env python3
"""
graph.py - Property Graph implementation using SQLite
C8 Challenge Level 3 (Gold)

Node types: Student, Challenge, Submission, Message, QAPair
Edge types: SUBMITTED, SENT, ASKED, ANSWERED, PROGRESSED_TO, TAGGED_WITH
"""

import json
import sqlite3
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).parent / "data" / "graph.db"


class PropertyGraph:
    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            id      TEXT PRIMARY KEY,
            type    TEXT NOT NULL,
            props   TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS edges (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            src     TEXT NOT NULL,
            dst     TEXT NOT NULL,
            type    TEXT NOT NULL,
            props   TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(src) REFERENCES nodes(id),
            FOREIGN KEY(dst) REFERENCES nodes(id)
        );
        CREATE INDEX IF NOT EXISTS idx_edges_src  ON edges(src);
        CREATE INDEX IF NOT EXISTS idx_edges_dst  ON edges(dst);
        CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
        CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
        """)
        self.conn.commit()

    # --- Node operations ---

    def add_node(self, node_id: str, node_type: str, **props) -> str:
        self.conn.execute(
            "INSERT OR REPLACE INTO nodes(id, type, props) VALUES (?, ?, ?)",
            (node_id, node_type, json.dumps(props, ensure_ascii=False)),
        )
        self.conn.commit()
        return node_id

    def get_node(self, node_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT id, type, props FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if not row:
            return None
        return {"id": row["id"], "type": row["type"], **json.loads(row["props"])}

    def update_node(self, node_id: str, **props):
        existing = self.get_node(node_id)
        if not existing:
            raise KeyError(f"Node {node_id!r} not found")
        merged = {k: v for k, v in existing.items() if k not in ("id", "type")}
        merged.update(props)
        self.conn.execute(
            "UPDATE nodes SET props = ? WHERE id = ?",
            (json.dumps(merged, ensure_ascii=False), node_id),
        )
        self.conn.commit()

    def find_nodes(self, node_type: str, **filters) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, type, props FROM nodes WHERE type = ?", (node_type,)
        ).fetchall()
        results = []
        for row in rows:
            node = {"id": row["id"], "type": row["type"], **json.loads(row["props"])}
            if all(node.get(k) == v for k, v in filters.items()):
                results.append(node)
        return results

    def all_nodes(self, node_type: str | None = None) -> list[dict]:
        if node_type:
            rows = self.conn.execute(
                "SELECT id, type, props FROM nodes WHERE type = ?", (node_type,)
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT id, type, props FROM nodes").fetchall()
        return [{"id": r["id"], "type": r["type"], **json.loads(r["props"])} for r in rows]

    # --- Edge operations ---

    def add_edge(self, src: str, dst: str, edge_type: str, **props) -> int:
        cur = self.conn.execute(
            "INSERT INTO edges(src, dst, type, props) VALUES (?, ?, ?, ?)",
            (src, dst, edge_type, json.dumps(props, ensure_ascii=False)),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_edges(self, src: str | None = None, dst: str | None = None,
                  edge_type: str | None = None) -> list[dict]:
        query = "SELECT id, src, dst, type, props FROM edges WHERE 1=1"
        params: list[Any] = []
        if src:
            query += " AND src = ?"
            params.append(src)
        if dst:
            query += " AND dst = ?"
            params.append(dst)
        if edge_type:
            query += " AND type = ?"
            params.append(edge_type)
        rows = self.conn.execute(query, params).fetchall()
        return [
            {"id": r["id"], "src": r["src"], "dst": r["dst"],
             "type": r["type"], **json.loads(r["props"])}
            for r in rows
        ]

    def get_neighbors(self, node_id: str, edge_type: str | None = None,
                      direction: str = "out") -> list[dict]:
        """Return neighbor nodes. direction: 'out', 'in', or 'both'."""
        results = []
        if direction in ("out", "both"):
            edges = self.get_edges(src=node_id, edge_type=edge_type)
            for e in edges:
                n = self.get_node(e["dst"])
                if n:
                    results.append(n)
        if direction in ("in", "both"):
            edges = self.get_edges(dst=node_id, edge_type=edge_type)
            for e in edges:
                n = self.get_node(e["src"])
                if n:
                    results.append(n)
        return results

    # --- Convenience methods ---

    def get_student_submissions(self, student_id: str) -> list[dict]:
        edges = self.get_edges(src=student_id, edge_type="SUBMITTED")
        return [self.get_node(e["dst"]) for e in edges if self.get_node(e["dst"])]

    def get_challenge_submitters(self, challenge_id: str) -> list[dict]:
        edges = self.get_edges(dst=challenge_id, edge_type="SUBMITTED")
        return [self.get_node(e["src"]) for e in edges if self.get_node(e["src"])]

    def get_student_message_count(self, student_id: str) -> int:
        return len(self.get_edges(src=student_id, edge_type="SENT"))

    def stats(self) -> dict:
        counts = {}
        for row in self.conn.execute(
            "SELECT type, COUNT(*) as cnt FROM nodes GROUP BY type"
        ).fetchall():
            counts[row["type"]] = row["cnt"]
        edge_counts = {}
        for row in self.conn.execute(
            "SELECT type, COUNT(*) as cnt FROM edges GROUP BY type"
        ).fetchall():
            edge_counts[row["type"]] = row["cnt"]
        return {"nodes": counts, "edges": edge_counts}

    def close(self):
        self.conn.close()
