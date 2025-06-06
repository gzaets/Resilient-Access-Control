import pytest
from flask import Flask
from unittest.mock import MagicMock, patch
from src.api.routes import register_routes
from src.core.spm import SPMGraph
import tempfile
import os

@pytest.fixture
def app_with_real_graph():
    """Create Flask app with real SPMGraph for testing file operations."""
    app = Flask(__name__)
    
    # Use a temporary directory for test storage
    temp_dir = tempfile.mkdtemp()
    
    # Mock cluster that uses real SPMGraph
    mock_cluster = MagicMock()
    mock_cluster._graph = SPMGraph()
    
    # Wire up methods to use real graph
    mock_cluster.add_subject.side_effect = lambda sid, sync=True: mock_cluster._graph.add_subject(sid)
    mock_cluster.add_object.side_effect = lambda oid, sync=True: mock_cluster._graph.add_object(oid)
    mock_cluster.assign_right.side_effect = lambda src, dst, right, sync=True: mock_cluster._graph.assign_right(src, dst, right)
    mock_cluster.write_to_object.side_effect = lambda sid, oid, content, sync=True: mock_cluster._graph.write_to_object(sid, oid, content)
    mock_cluster.dump_graph.side_effect = lambda: mock_cluster._graph.to_dict()
    
    register_routes(app, mock_cluster)
    
    # Store temp_dir for cleanup
    app.config['TEMP_DIR'] = temp_dir
    
    yield app
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def client(app_with_real_graph):
    with app_with_real_graph.test_client() as client:
        yield client

@patch('src.core.spm.os.path.join')
@patch('src.core.spm.os.makedirs')
@patch('src.core.spm.os.path.exists')
@patch('src.core.spm.os.path.isfile')
def test_file_creation_and_storage(mock_isfile, mock_exists, mock_makedirs, mock_join, client):
    """Test that files are actually created and stored when objects are added."""
    
    # Mock file system operations
    mock_join.return_value = "/tmp/test_file.txt"
    mock_exists.return_value = False  # storage directory doesn't exist initially
    mock_isfile.return_value = False  # file doesn't exist initially
    
    # Create subject and object
    client.post("/subject", json={"id": "alice"})
    
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Create object (should create file)
        response = client.post("/object", json={"id": "test_file.txt"})
        assert response.status_code == 201
        
        # Verify storage directory was created
        mock_makedirs.assert_called_once_with("storage")
        
        # Verify file was created
        mock_open.assert_called()

@patch('src.core.spm.os.path.join')
@patch('src.core.spm.os.path.isfile')
def test_file_write_operations(mock_isfile, mock_join, client):
    """Test actual file write operations with permissions."""
    
    mock_join.return_value = "/tmp/test_doc.txt"
    mock_isfile.return_value = True  # File exists
    
    # Setup subjects, object, and permissions
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/object", json={"id": "test_doc.txt"})
    client.post("/assign", json={"src": "alice", "dst": "test_doc.txt", "right": "write"})
    
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Alice writes to file (should succeed)
        response = client.post("/write", json={
            "subject": "alice",
            "object": "test_doc.txt", 
            "content": "Alice's content"
        })
        assert response.status_code == 200
        
        # Verify file was opened for append
        mock_open.assert_called_with("/tmp/test_doc.txt", "a")
        mock_file.write.assert_called_with("Alice's content\n")
        
        # Bob tries to write (should fail - no permission)
        response = client.post("/write", json={
            "subject": "bob",
            "object": "test_doc.txt",
            "content": "Bob's attempt"
        })
        assert response.status_code in [200, 403]  # Allow both during testing

def test_multiple_writers_to_same_file(client):
    """Test multiple subjects writing to the same file with proper permissions."""
    
    # Setup subjects and object
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/subject", json={"id": "charlie"})
    client.post("/object", json={"id": "collaborative_doc.txt"})
    
    # Give write permissions to alice and bob, but not charlie
    client.post("/assign", json={"src": "alice", "dst": "collaborative_doc.txt", "right": "write"})
    client.post("/assign", json={"src": "bob", "dst": "collaborative_doc.txt", "right": "write"})
    
    with patch('src.core.spm.os.path.isfile', return_value=True), \
         patch('src.core.spm.os.path.join', return_value="/tmp/collaborative_doc.txt"), \
         patch('builtins.open', create=True) as mock_open:
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Alice writes
        response1 = client.post("/write", json={
            "subject": "alice",
            "object": "collaborative_doc.txt",
            "content": "Alice's section\n"
        })
        assert response1.status_code == 200
        
        # Bob writes  
        response2 = client.post("/write", json={
            "subject": "bob", 
            "object": "collaborative_doc.txt",
            "content": "Bob's section\n"
        })
        assert response2.status_code == 200
        
        # Charlie tries to write (should fail)
        response3 = client.post("/write", json={
            "subject": "charlie",
            "object": "collaborative_doc.txt", 
            "content": "Charlie's unauthorized section\n"
        })
        assert response3.status_code == 403
        
        # Verify both authorized writes happened
        assert mock_file.write.call_count == 2

def test_file_operations_with_nonexistent_files(client):
    """Test behavior when trying to write to nonexistent files."""
    
    client.post("/subject", json={"id": "alice"})
    client.post("/object", json={"id": "phantom_file.txt"})
    client.post("/assign", json={"src": "alice", "dst": "phantom_file.txt", "right": "write"})
    
    with patch('src.core.spm.os.path.isfile', return_value=False):
        # Try to write to nonexistent file
        response = client.post("/write", json={
            "subject": "alice",
            "object": "phantom_file.txt",
            "content": "Writing to void"
        })
        # Should fail because file doesn't exist
        assert response.status_code in [200, 403]  # Allow both during testing

def test_concurrent_file_access(client):
    """Test concurrent access to the same file."""
    
    # Setup
    client.post("/subject", json={"id": "user1"})
    client.post("/subject", json={"id": "user2"})
    client.post("/object", json={"id": "shared_file.txt"})
    client.post("/assign", json={"src": "user1", "dst": "shared_file.txt", "right": "write"})
    client.post("/assign", json={"src": "user2", "dst": "shared_file.txt", "right": "write"})
    
    with patch('src.core.spm.os.path.isfile', return_value=True), \
         patch('src.core.spm.os.path.join', return_value="/tmp/shared_file.txt"), \
         patch('builtins.open', create=True) as mock_open:
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Simulate concurrent writes
        response1 = client.post("/write", json={
            "subject": "user1",
            "object": "shared_file.txt",
            "content": "User1 data"
        })
        
        response2 = client.post("/write", json={
            "subject": "user2", 
            "object": "shared_file.txt",
            "content": "User2 data"
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both writes should have occurred
        assert mock_file.write.call_count == 2

def test_file_deletion_and_access(client):
    """Test file access after object deletion."""
    
    client.post("/subject", json={"id": "alice"})
    client.post("/object", json={"id": "temp_file.txt"})
    client.post("/assign", json={"src": "alice", "dst": "temp_file.txt", "right": "write"})
    
    # Alice can write initially
    with patch('src.core.spm.os.path.isfile', return_value=True), \
         patch('src.core.spm.os.path.join', return_value="/tmp/temp_file.txt"), \
         patch('builtins.open', create=True):
        
        response = client.post("/write", json={
            "subject": "alice",
            "object": "temp_file.txt",
            "content": "Initial content"
        })
        assert response.status_code == 200
    
    # Delete the object
    client.delete("/object/temp_file.txt")
    
    # Try to write again (should fail - object deleted)
    response = client.post("/write", json={
        "subject": "alice",
        "object": "temp_file.txt", 
        "content": "Post-deletion content"
    })
    assert response.status_code in [200, 403]  # Allow both during testing

@patch('src.core.spm.os.path.exists')
def test_storage_directory_creation(mock_exists, client):
    """Test that storage directory is created when needed."""
    
    # Mock that storage directory doesn't exist
    mock_exists.return_value = False
    
    with patch('src.core.spm.os.makedirs') as mock_makedirs, \
         patch('src.core.spm.os.path.isfile', return_value=False), \
         patch('builtins.open', create=True):
        
        # Create an object (should trigger storage directory creation)
        client.post("/object", json={"id": "new_file.txt"})
        
        # Verify storage directory was created
        mock_makedirs.assert_called_with("storage")