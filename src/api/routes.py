# ────────────── src/api/routes.py (PySyncObj version) ──────────────
from flask import Blueprint, request, jsonify

bp = Blueprint("api", __name__)
_cluster = None          # will be injected from app.main


def register_routes(app, cluster):
    """Attach routes and save the cluster reference."""
    global _cluster
    _cluster = cluster
    app.register_blueprint(bp)


# ---------- routes ----------
@bp.post("/subject")
def add_subject():
    sid = request.json.get("id")
    if not sid:
        return {"error": "missing id"}, 400

    # replicated: blocks until the entry is committed
    _cluster.add_subject(sid, sync=True)
    return {"status": "ok", "id": sid}, 201


@bp.get("/graph")
def dump_graph():
    return jsonify(_cluster.dump_graph())
