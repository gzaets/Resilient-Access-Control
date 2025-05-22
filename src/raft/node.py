# ────────────── src/raft/node.py (PySyncObj version) ──────────────
from pysyncobj import SyncObj, replicated
from src.core.spm import SPMGraph


class GraphCluster(SyncObj):
    """
    A replicated wrapper around SPMGraph.
    All mutating methods are marked @replicated so they
    are appended to the Raft log and executed on every node.
    """

    def __init__(self, self_addr: str, partner_addrs: list[str]) -> None:
        super().__init__(self_addr, partner_addrs)
        self._graph = SPMGraph()

    # ---------- replicated mutations ----------
    @replicated
    def add_subject(self, sid: str) -> None:
        self._graph.add_subject(sid)

    # ---------- local helpers ----------
    def dump_graph(self) -> dict:
        """Return a JSON-serialisable view of the current graph."""
        return self._graph.to_dict()


def setup_cluster(self_addr: str, partner_addrs: list[str]) -> GraphCluster:
    """
    Initialise the PySyncObj cluster and return the cluster object
    so the REST layer can call replicated methods on it.
    """
    return GraphCluster(self_addr, partner_addrs)
