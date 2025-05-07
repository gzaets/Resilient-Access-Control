# src/app/main.py

"""
    Summary of the module:
    - This module serves as the entry point for a Flask application that uses Raft consensus for distributed state management.
    - It sets up the Flask app, configures Raft, and registers API routes.
        - Flask is a micro web framework for Python, used to build web applications.
        - It provides a simple way to create RESTful APIs.
    - The Raft consensus algorithm is used to ensure that the state of the application is consistent across multiple nodes.
    - The application is designed to run in a Docker container, with the node ID and peer IDs being configurable through environment variables.
    - The Flask app is set to run on all interfaces at port 5000.
    - The main function initializes the Raft node and starts the Flask application.
        - The Raft consensus algorithm is used to ensure that the state of the application is consistent across multiple nodes.
"""

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
