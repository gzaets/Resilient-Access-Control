# src/app/main.py
import os, asyncio
from flask import Flask
from api.routes import bp                      # blueprint already initialises Raft!

app = Flask(__name__)
app.register_blueprint(bp)

if __name__ == "__main__":
    # Nothing else needed: raft ticker already scheduled in node.py
    app.run(host="0.0.0.0", port=5000, debug=False)
