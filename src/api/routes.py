# src/api/routes.py
"""
Flask API endpoints + replication glue using pysyncobj.
We store the whole SPM graph under the replicated key 'graph'.
"""

import asyncio, json
from flask import Blueprint, jsonify, request

from core.spm import SPMGraph
from raft.node import init_raft_from_env

bp          = Blueprint("api", __name__)
raft_node   = init_raft_from_env()       # global singleton
graph       = SPMGraph()                 # local in-memory copy


# ---------- helpers -------------------------------------------------------
async def _pull_graph_from_cluster():
    """Fetch latest replicated graph every second."""
    while True:
        data = raft_node.get("graph")
        if data:
            global graph
            graph = SPMGraph.from_dict(data)
        await asyncio.sleep(1)


asyncio.get_event_loop().create_task(_pull_graph_from_cluster())


def _push_graph():
    """Replicate local graph -> cluster."""
    raft_node.put("graph", graph.to_dict())


# ---------- routes --------------------------------------------------------
@bp.post("/subject")
def add_subject():
    sid = request.json.get("id")
    if not sid:
        return {"error": "missing id"}, 400

    graph.add_subject(sid)
    _push_graph()
    return {"status": "ok", "id": sid}, 201


@bp.get("/graph")
def dump_graph():
    return jsonify(graph.to_dict())
