# src/api/routes.py
from flask import Blueprint, request, jsonify
from core.spm import SPMGraph
import raftos, asyncio

bp     = Blueprint("api", __name__)
graph  = SPMGraph()                      # local in‑memory
gstore = raftos.Replicated(name="graph") # one Raft key for the whole graph

def register_routes(app):
    app.register_blueprint(bp)

# ---------- helper to keep replicas fresh ----------
async def _sync_to_local():
    gdict = await gstore.get(default=None)
    if gdict:
        global graph
        graph = SPMGraph.from_dict(gdict)

# Poll every second
asyncio.get_event_loop().create_task(
    raftos.utils.schedule(_sync_to_local, interval=1)
)

# ---------- routes ----------
@bp.post("/subject")
def add_subject():
    sid = request.json.get("id")
    if not sid:
        return {"error": "missing id"}, 400

    graph.add_subject(sid)

    # replicate
    asyncio.get_event_loop().create_task(gstore.set(graph.to_dict()))
    return {"status": "ok", "id": sid}, 201


@bp.get("/graph")
def dump_graph():
    return jsonify(graph.to_dict())
