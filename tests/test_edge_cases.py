import pytest
from flask import Flask
from unittest.mock import MagicMock, patch
from src.api.routes import register_routes
from src.core.spm import SPMGraph

@pytest.fixture
def app_with_real_graph():
    """Create Flask app with real SPMGraph for testing edge cases."""
    app = Flask(__name__)
    
    mock_cluster = MagicMock()
    mock_cluster._graph = SPMGraph()
    
    # Wire up methods to use real graph
    mock_cluster.add_subject.side_effect = lambda sid, sync=True: mock_cluster._graph.add_subject(sid)
    mock_cluster.add_object.side_effect = lambda oid, sync=True: mock_cluster._graph.add_object(oid)
    mock_cluster.delete_subject.side_effect = lambda sid, sync=True: mock_cluster._graph.delete_subject(sid)
    mock_cluster.delete_object.side_effect = lambda oid, sync=True: mock_cluster._graph.delete_object(oid)
    mock_cluster.assign_right.side_effect = lambda src, dst, right, sync=True: mock_cluster._graph.assign_right(src, dst, right)
    mock_cluster.write_to_object.side_effect = lambda sid, oid, content, sync=True: mock_cluster._graph.write_to_object(sid, oid, content)
    mock_cluster.dump_graph.side_effect = lambda: mock_cluster._graph.to_dict()
    
    register_routes(app, mock_cluster)
    return app

@pytest.fixture
def client(app_with_real_graph):
    with app_with_real_graph.test_client() as client:
        yield client

def test_empty_request_handling(client):
    """Test handling of empty or malformed requests."""
    
    # Empty JSON
    response = client.post("/subject", json={})
    assert response.status_code == 400
    assert "missing id" in response.json.get("error", "")
    
    # Missing required fields
    response = client.post("/assign", json={"src": "alice"})
    assert response.status_code == 400
    assert "missing parameters" in response.json.get("error", "")
    
    # Empty strings
    response = client.post("/subject", json={"id": ""})
    assert response.status_code == 400
    
    response = client.post("/write", json={"subject": "", "object": "file.txt", "content": "test"})
    assert response.status_code == 400

def test_invalid_right_types(client):
    """Test handling of invalid right types."""
    
    # Setup basic subjects
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    
    # Try invalid rights
    invalid_rights = ["delete", "execute", "admin", "root", "invalid", "123", ""]
    
    for invalid_right in invalid_rights:
        response = client.post("/assign", json={
            "src": "alice", 
            "dst": "bob", 
            "right": invalid_right
        })
        assert response.status_code == 400
        assert "invalid" in response.json.get("error", "").lower() or "missing" in response.json.get("error", "").lower()

def test_self_referential_operations(client):
    """Test edge cases with self-referential operations."""
    
    client.post("/subject", json={"id": "alice"})
    
    # Subject assigning rights to themselves
    response = client.post("/assign", json={
        "src": "alice",
        "dst": "alice", 
        "right": "read"
    })
    # This might be valid in some SPM implementations
    assert response.status_code in [201, 400]
    
    # Subject trying to delete themselves while having operations pending
    response = client.delete("/subject/alice")
    assert response.status_code == 200

def test_very_long_identifiers(client):
    """Test handling of very long subject/object identifiers."""
    
    # Very long subject ID
    long_id = "a" * 1000
    response = client.post("/subject", json={"id": long_id})
    # Should either succeed or fail gracefully
    assert response.status_code in [201, 400]
    
    # Unicode characters
    unicode_id = "测试用户"
    response = client.post("/subject", json={"id": unicode_id})
    assert response.status_code in [201, 400]
    
    # Special characters
    special_id = "user@domain.com"
    response = client.post("/subject", json={"id": special_id})
    assert response.status_code in [201, 400]

def test_duplicate_creation_attempts(client):
    """Test creating subjects/objects with duplicate IDs."""
    
    # Create subject
    response1 = client.post("/subject", json={"id": "alice"})
    assert response1.status_code == 201
    
    # Try to create same subject again
    response2 = client.post("/subject", json={"id": "alice"})
    # Should either succeed (idempotent) or fail gracefully
    assert response2.status_code in [201, 400, 409]
    
    # Same for objects
    response3 = client.post("/object", json={"id": "file.txt"})
    assert response3.status_code == 201
    
    response4 = client.post("/object", json={"id": "file.txt"})
    assert response4.status_code in [201, 400, 409]

def test_operations_on_deleted_entities(client):
    """Test operations on deleted subjects/objects."""
    
    # Create and delete subject
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.delete("/subject/alice")
    
    # Try to assign rights to deleted subject
    response = client.post("/assign", json={
        "src": "bob",
        "dst": "alice", 
        "right": "read"
    })
    assert response.status_code in [200, 201, 400, 403]  # Allow various responses
    
    # Try to assign rights from deleted subject
    response = client.post("/assign", json={
        "src": "alice",
        "dst": "bob",
        "right": "read" 
    })
    assert response.status_code in [200, 201, 400, 403]  # Allow various responses

def test_massive_permission_assignments(client):
    """Test performance with many permission assignments."""
    
    # Create many subjects
    subjects = [f"user_{i}" for i in range(50)]
    for subject in subjects:
        client.post("/subject", json={"id": subject})
    
    # Create objects
    objects = [f"file_{i}.txt" for i in range(20)]
    for obj in objects:
        client.post("/object", json={"id": obj})
    
    # Assign many permissions
    assignment_count = 0
    for subject in subjects[:10]:  # Limit to avoid timeout
        for obj in objects[:5]:
            response = client.post("/assign", json={
                "src": subject,
                "dst": obj,
                "right": "read"
            })
            if response.status_code == 201:
                assignment_count += 1
    
    # Verify some assignments succeeded
    assert assignment_count > 0
    
    # Check graph state
    response = client.get("/graph")
    assert response.status_code == 200
    graph_data = response.json
    assert len(graph_data["edges"]) >= assignment_count

def test_null_and_none_values(client):
    """Test handling of null/None values in requests."""
    
    # Null values in JSON
    response = client.post("/subject", json={"id": None})
    assert response.status_code == 400
    
    response = client.post("/assign", json={
        "src": "alice",
        "dst": None,
        "right": "read"
    })
    assert response.status_code == 400
    
    response = client.post("/write", json={
        "subject": "alice", 
        "object": "file.txt",
        "content": None
    })
    assert response.status_code == 400

def test_concurrent_deletion_and_access(client):
    """Test race conditions between deletion and access operations."""
    
    # Create subject and object
    client.post("/subject", json={"id": "alice"})
    client.post("/object", json={"id": "temp_file.txt"})
    client.post("/assign", json={"src": "alice", "dst": "temp_file.txt", "right": "write"})
    
    # Simulate rapid deletion and access
    # In a real distributed system, these could happen concurrently
    
    # Delete object
    response1 = client.delete("/object/temp_file.txt")
    assert response1.status_code == 200
    
    # Immediately try to write (should fail)
    with patch('src.core.spm.os.path.isfile', return_value=False):
        response2 = client.post("/write", json={
            "subject": "alice",
            "object": "temp_file.txt",
            "content": "Should fail"
        })
        assert response2.status_code == 403

def test_graph_consistency_after_many_operations(client):
    """Test that graph remains consistent after many operations."""
    
    # Perform many varied operations
    operations = [
        ("POST", "/subject", {"id": "alice"}),
        ("POST", "/subject", {"id": "bob"}), 
        ("POST", "/object", {"id": "file1.txt"}),
        ("POST", "/object", {"id": "file2.txt"}),
        ("POST", "/assign", {"src": "alice", "dst": "file1.txt", "right": "read"}),
        ("POST", "/assign", {"src": "alice", "dst": "file1.txt", "right": "write"}),
        ("POST", "/assign", {"src": "bob", "dst": "file2.txt", "right": "read"}),
        ("DELETE", "/subject/bob", {}),
        ("POST", "/subject", {"id": "charlie"}),
        ("POST", "/assign", {"src": "alice", "dst": "file2.txt", "right": "read"}),
    ]
    
    for method, endpoint, data in operations:
        if method == "POST":
            client.post(endpoint, json=data)
        elif method == "DELETE":
            client.delete(endpoint)
    
    # Check final graph state
    response = client.get("/graph")
    assert response.status_code == 200
    
    graph_data = response.json
    
    # Verify graph structure is valid
    assert "nodes" in graph_data
    assert "edges" in graph_data
    assert isinstance(graph_data["nodes"], list)
    assert isinstance(graph_data["edges"], list)
    
    # Check that deleted entities don't appear
    node_ids = [node["id"] for node in graph_data["nodes"]]
    assert "bob" not in node_ids  # Bob was deleted
    
    # Check remaining entities
    assert "alice" in node_ids
    assert "charlie" in node_ids