# ────────────── src/app/main.py ──────────────
import os
from flask import Flask

from src.raft.node import setup_cluster
from src.api.routes import register_routes

# addresses come from the environment (see docker-run commands below)
SELF_ADDR = os.getenv("SELF_ADDR", "node1:4321")
PARTNERS  = [p for p in os.getenv("PARTNERS", "").split(",") if p]

# --- PySyncObj cluster ----------------------------------------------------
cluster = setup_cluster(SELF_ADDR, PARTNERS)

# --- Flask app ------------------------------------------------------------
app = Flask(__name__)
register_routes(app, cluster)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
