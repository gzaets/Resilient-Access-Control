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

@bp.post("/object")
def add_object():
    oid = request.json.get("id")
    if not oid:
        return {"error": "missing id"}, 400

    _cluster.add_object(oid, sync=True)
    return {"status": "ok", "id": oid}, 201


@bp.delete("/subject/<sid>")
def delete_subject(sid):
    _cluster.delete_subject(sid, sync=True)
    return {"status": "ok", "id": sid}, 200


@bp.delete("/object/<oid>")
def delete_object(oid):
    _cluster.delete_object(oid, sync=True)
    return {"status": "ok", "id": oid}, 200


@bp.post("/assign")
def assign_right():
    data = request.json
    src = data.get("src")
    dst = data.get("dst")
    right = data.get("right")

    if not src or not dst or not right:
        return {"error": "missing parameters"}, 400

    # Validate the right parameter
    valid_rights = {"read", "write", "execute"}  # Example valid rights
    if right not in valid_rights:
        return {"error": "invalid operation"}, 400

    if _cluster.assign_right(src, dst, right, sync=True):
        return {"status": "ok", "src": src, "dst": dst, "right": right}, 201
    return {"error": "invalid operation"}, 400


@bp.get("/graph")
def dump_graph():
    return jsonify(_cluster.dump_graph())


@bp.post("/write")
def write_to_file():
    data = request.json
    sid = data.get("subject")
    oid = data.get("object")
    content = data.get("content")

    if not sid or not oid or not content:
        return {"error": "missing parameters"}, 400

    if _cluster.write_to_object(sid, oid, content, sync=True):
        return {"status": "written", "object": oid}, 200
    return {"error": "write denied or failed"}, 403
