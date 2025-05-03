# src/app/main.py
import os
from flask import Flask
from api.routes import register_routes
from raft.node import setup_raft

NODE_ID = os.getenv("NODE_ID", "node1")
PEERS   = os.getenv("PEERS",  "node2,node3").split(",")

# --- Raft first -----------------------------------------------------------
setup_raft(node_id=NODE_ID, peer_ids=PEERS)

# --- Flask app ------------------------------------------------------------
app = Flask(__name__)
register_routes(app)

if __name__ == "__main__":
    # gunicorn/uvicorn not needed inside Docker; plain run is fine
    app.run(host="0.0.0.0", port=5000, debug=False)
