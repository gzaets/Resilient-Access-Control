# src/raft/node.py
"""
PySyncObj wrapper used by the whole app.

* Creates one global replicated key-value store (`raft.kv`)
* Exposes replicated put()/get() helpers for other modules
* Starts a background onTick() task so PySyncObj makes progress
"""

from __future__ import annotations

import asyncio, json, os
from typing import List

from pysyncobj import SyncObj, SyncObjConf, replicated
from pysyncobj.batteries import ReplDict


class RACNode(SyncObj):
    """Replicated key–value store (string → string) for RAC-NAS."""

    def __init__(self, self_addr: str, partner_addrs: List[str]):
        self.kv: ReplDict[str, str] = ReplDict()
        conf = SyncObjConf(autoTick=False)  # we tick manually in an asyncio task
        super().__init__(self_addr, partner_addrs, consumers=[self.kv], conf=conf)

    # ---------- replicated ops ----------
    @replicated
    def _put(self, k: str, v: str) -> None:
        self.kv[k] = v

    # ---------- public helpers ----------
    def put(self, k: str, v: dict) -> None:
        """Replicate any JSON-serialisable dict."""
        self._put(k, json.dumps(v))

    def get(self, k: str, default=None):
        v = self.kv.get(k, None)
        if v is None:
            return default
        return json.loads(v)


# ---- global singleton ----------------------------------------------------
_raft: RACNode | None = None


def init_raft_from_env() -> RACNode:
    """
    Initialise the singleton RACNode from ENV:

    * SELF_ADDR  – this node's addr,  e.g.  node1:4321
    * PARTNERS   – comma-separated partner addrs (may be empty)
    """
    global _raft
    if _raft:
        return _raft

    self_addr = os.getenv("SELF_ADDR", "node1:4321")
    partners  = [p for p in os.getenv("PARTNERS", "").split(",") if p]
    _raft = RACNode(self_addr, partners)

    # background ticker so PySyncObj progresses inside asyncio loop
    async def _ticker():
        while True:
            _raft.onTick()
            await asyncio.sleep(0.05)

    asyncio.get_event_loop().create_task(_ticker())
    print(f"[RAFT] self={self_addr}, partners={partners}")
    return _raft
