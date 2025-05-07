# src/core/spm.py
"""
    Summary of the module:
    - This module implements a minimal SPM Graph engine.
    - It uses NetworkX's DiGraph to represent the graph structure.
    - Nodes in the graph are represented as dictionaries with a "type" key indicating whether they are a subject or an object.
    - Edges in the graph carry a set of rights, which can include "read", "write", "take", and "grant".
    - The module provides methods to add subjects and objects, grant and take rights, and check if a right exists.
    - It also includes a method to serialize the graph to a dictionary format for JSON serialization.
    - The graph is designed to be used in a distributed system, with the ability to replicate its state using Raft consensus.
    - The `SPMGraph` class provides the main functionality for managing the graph and its rights.

    Minimal SPM Graph engine.
    Uses NetworkX DiGraph where:
    - Nodes are dicts with {"type": "subject" | "object"}
    - Edges carry a set of rights: {"read", "write", "take", "grant"}
"""

import networkx as nx

RIGHTS = {"read", "write", "take", "grant"}


class SPMGraph:
    def __init__(self) -> None:
        self.g = nx.DiGraph()

    # ---------- node helpers ---------- #
    def add_subject(self, sid: str) -> None:
        self.g.add_node(sid, type="subject")

    def add_object(self, oid: str) -> None:
        self.g.add_node(oid, type="object")

    # ---------- rights helpers ---------- #
    def _ensure_edge(self, src, dst):
        if not self.g.has_edge(src, dst):
            self.g.add_edge(src, dst, rights=set())

    def grant(self, granter: str, grantee: str, right: str, target: str) -> bool:
        """
        granter ≈ subject holding 'grant' + <right> on target
        grantee ≈ subject receiving <right> on target
        """
        if right not in RIGHTS:
            return False
        if not self.has_right(granter, target, "grant") or not self.has_right(
            granter, target, right
        ):
            return False  # no authority
        self._ensure_edge(grantee, target)
        self.g[grantee][target]["rights"].add(right)
        return True

    def take(self, taker: str, source: str, right: str, target: str) -> bool:
        """
        taker takes <right> on target from source if source currently holds it
        and taker has 'take' over source.
        """
        if not self.has_right(taker, source, "take"):
            return False
        if not self.has_right(source, target, right):
            return False
        self._ensure_edge(taker, target)
        self.g[taker][target]["rights"].add(right)
        return True

    def has_right(self, src: str, dst: str, right: str) -> bool:
        return (
            self.g.has_edge(src, dst)
            and right in self.g[src][dst].get("rights", set())
        )

    # ---------- serialization ---------- #
    def to_dict(self):
        """Return dict for JSON serialization."""
        return {
            "nodes": [
                {"id": n, "type": d["type"]} for n, d in self.g.nodes(data=True)
            ],
            "edges": [
                {"src": u, "dst": v, "rights": list(d["rights"])}
                for u, v, d in self.g.edges(data=True)
            ],
        }
