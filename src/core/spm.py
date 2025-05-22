# ────────────── src/core/spm.py ──────────────
import networkx as nx

RIGHTS = {"read", "write", "take", "grant"}


class SPMGraph:
    def __init__(self) -> None:
        self.g = nx.DiGraph()

    # ---------- node helpers ----------
    def add_subject(self, sid: str) -> None:
        self.g.add_node(sid, type="subject")

    def add_object(self, oid: str) -> None:
        self.g.add_node(oid, type="object")

    # ---------- rights helpers ----------
    def _ensure_edge(self, src, dst):
        if not self.g.has_edge(src, dst):
            self.g.add_edge(src, dst, rights=set())

    def grant(self, granter, grantee, right, target) -> bool:
        if right not in RIGHTS:
            return False
        if not self.has_right(granter, target, "grant") or not self.has_right(
            granter, target, right
        ):
            return False
        self._ensure_edge(grantee, target)
        self.g[grantee][target]["rights"].add(right)
        return True

    def take(self, taker, source, right, target) -> bool:
        if not self.has_right(taker, source, "take"):
            return False
        if not self.has_right(source, target, right):
            return False
        self._ensure_edge(taker, target)
        self.g[taker][target]["rights"].add(right)
        return True

    def has_right(self, src, dst, right) -> bool:
        return (
            self.g.has_edge(src, dst)
            and right in self.g[src][dst].get("rights", set())
        )

    # ---------- serialisation ----------
    def to_dict(self) -> dict:
        return {
            "nodes": [
                {"id": n, "type": d["type"]} for n, d in self.g.nodes(data=True)
            ],
            "edges": [
                {"src": u, "dst": v, "rights": list(d["rights"])}
                for u, v, d in self.g.edges(data=True)
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SPMGraph":
        g = cls()
        for node in data.get("nodes", []):
            g.g.add_node(node["id"], type=node["type"])
        for edge in data.get("edges", []):
            g.g.add_edge(edge["src"], edge["dst"], rights=set(edge["rights"]))
        return g
