import pytest
from flask import Flask
from src.api.routes import register_routes
from src.raft.node import GraphCluster

@pytest.fixture
def client():
    app = Flask(__name__)
    cluster = GraphCluster("node1:4321", [])
    register_routes(app, cluster)
    with app.test_client() as client:
        yield client

def test_add_subject(client):
    response = client.post("/subject", json={"id": "alice"})
    assert response.status_code == 201
    assert response.json == {"status": "ok", "id": "alice"}

def test_delete_subject(client):
    client.post("/subject", json={"id": "alice"})
    response = client.delete("/subject/alice")
    assert response.status_code == 200
    assert response.json == {"status": "ok", "id": "alice"}

def test_assign_right(client):
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    response = client.post("/assign", json={"src": "alice", "dst": "bob", "right": "read"})
    assert response.status_code == 201
    assert response.json == {"status": "ok", "src": "alice", "dst": "bob", "right": "read"}

def test_invalid_assign_right(client):
    response = client.post("/assign", json={"src": "alice", "dst": "bob", "right": "invalid_right"})
    assert response.status_code == 400
    assert response.json == {"error": "invalid operation"}
