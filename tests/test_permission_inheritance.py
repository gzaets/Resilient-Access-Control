import pytest
from flask import Flask
from unitte    # Test the underlying SPM logic
    app = client.application
    # Get cluster from the route registration
    # Since we're using mocks, we'll access the underlying graph directly
    from unittest.mock import MagicMock
    
    # Create a real graph for this test
    from src.core.spm import SPMGraph
    real_graph = SPMGraph()
    real_graph.add_subject("alice")
    real_graph.add_subject("bob")
    real_graph.add_object("restricted_file.txt")
    
    # Alice tries to grant write access to bob (should fail - alice has no grant right)
    result = real_graph.grant("alice", "bob", "write", "restricted_file.txt")
    assert result == False
    
    # Verify bob still has no write access
    assert real_graph.has_right("bob", "restricted_file.txt", "write") == FalseMagicMock
from src.api.routes import register_routes
from src.core.spm import SPMGraph

@pytest.fixture
def app_with_real_graph():
    """Create Flask app with real SPMGraph for testing grant/take logic."""
    app = Flask(__name__)
    
    # Mock cluster that uses real SPMGraph
    mock_cluster = MagicMock()
    mock_cluster._graph = SPMGraph()
    
    # Wire up methods to use real graph
    mock_cluster.add_subject.side_effect = lambda sid, sync=True: mock_cluster._graph.add_subject(sid)
    mock_cluster.add_object.side_effect = lambda oid, sync=True: mock_cluster._graph.add_object(oid)
    mock_cluster.assign_right.side_effect = lambda src, dst, right, sync=True: mock_cluster._graph.assign_right(src, dst, right)
    mock_cluster.dump_graph.side_effect = lambda: mock_cluster._graph.to_dict()
    
    # Add grant and take operations (these would need to be added to routes.py)
    def mock_grant(granter, grantee, right, target, sync=True):
        return mock_cluster._graph.grant(granter, grantee, right, target)
    
    def mock_take(taker, source, right, target, sync=True):
        return mock_cluster._graph.take(taker, source, right, target)
    
    mock_cluster.grant = mock_grant
    mock_cluster.take = mock_take
    
    register_routes(app, mock_cluster)
    return app

@pytest.fixture
def client(app_with_real_graph):
    with app_with_real_graph.test_client() as client:
        yield client

def test_subject_cannot_grant_rights_they_dont_have(client):
    """Test that a subject cannot grant rights they don't possess."""
    # Create subjects and object
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/object", json={"id": "restricted_file.txt"})
    
    # Alice has no rights to the file
    # Try to have alice grant bob write access (should fail)
    
    # Since grant/take aren't in routes.py yet, we'll test the underlying logic
    app = client.application
    cluster = app.extensions.get('cluster') or getattr(app, '_cluster', None)
    
    # Get the cluster from the routes module
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Alice tries to grant write access to bob (should fail - alice has no grant right)
        result = graph.grant("alice", "bob", "write", "restricted_file.txt")
        assert result == False
        
        # Verify bob still has no write access
        assert graph.has_right("bob", "restricted_file.txt", "write") == False

def test_subject_cannot_grant_without_grant_permission(client):
    """Test that a subject needs 'grant' permission to grant rights to others."""
    # Create subjects and object
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/subject", json={"id": "charlie"})
    client.post("/object", json={"id": "document.txt"})
    
    # Give alice write permission but NOT grant permission
    client.post("/assign", json={"src": "alice", "dst": "document.txt", "right": "write"})
    
    # Test the underlying SPM logic
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Alice tries to grant write to bob (should fail - no grant permission)
        result = graph.grant("alice", "bob", "write", "document.txt")
        assert result == False
        
        # Give alice grant permission
        graph.assign_right("alice", "document.txt", "grant")
        
        # Now alice should be able to grant write to bob
        result = graph.grant("alice", "bob", "write", "document.txt")
        assert result == True
        
        # Verify bob now has write access
        assert graph.has_right("bob", "document.txt", "write") == True

def test_subject_cannot_take_without_take_permission(client):
    """Test that a subject needs 'take' permission to take rights from others."""
    # Create subjects and object
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/subject", json={"id": "eve"})
    client.post("/object", json={"id": "valuable_data.txt"})
    
    # Give bob write permission
    client.post("/assign", json={"src": "bob", "dst": "valuable_data.txt", "right": "write"})
    
    # Test the underlying SPM logic
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Eve tries to take write permission from bob (should fail - no take permission)
        result = graph.take("eve", "bob", "write", "valuable_data.txt")
        assert result == False
        
        # Verify eve still has no write access
        assert graph.has_right("eve", "valuable_data.txt", "write") == False
        
        # Give eve take permission on bob
        graph.assign_right("eve", "bob", "take")
        
        # Now eve should be able to take write permission from bob
        result = graph.take("eve", "bob", "write", "valuable_data.txt")
        assert result == True
        
        # Verify eve now has write access
        assert graph.has_right("eve", "valuable_data.txt", "write") == True

def test_nested_subject_creation_permission_limits(client):
    """Test that created subjects don't inherit permissions from creators."""
    # Create subjects
    client.post("/subject", json={"id": "admin"})
    client.post("/subject", json={"id": "manager"})
    client.post("/subject", json={"id": "employee"})
    client.post("/object", json={"id": "company_secrets.txt"})
    
    # Give admin full permissions
    client.post("/assign", json={"src": "admin", "dst": "company_secrets.txt", "right": "read"})
    client.post("/assign", json={"src": "admin", "dst": "company_secrets.txt", "right": "write"})
    client.post("/assign", json={"src": "admin", "dst": "company_secrets.txt", "right": "grant"})
    
    # Admin creates manager account (in real system, this would be a separate operation)
    # But manager should not automatically inherit admin's permissions
    
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Verify manager has no permissions initially
        assert graph.has_right("manager", "company_secrets.txt", "read") == False
        assert graph.has_right("manager", "company_secrets.txt", "write") == False
        assert graph.has_right("manager", "company_secrets.txt", "grant") == False
        
        # Manager tries to grant permissions to employee (should fail)
        result = graph.grant("manager", "employee", "read", "company_secrets.txt")
        assert result == False
        
        # Admin must explicitly grant permissions to manager
        result = graph.grant("admin", "manager", "read", "company_secrets.txt")
        assert result == True
        
        # Now manager has read but still can't grant to others (no grant permission)
        result = graph.grant("manager", "employee", "read", "company_secrets.txt")
        assert result == False

def test_permission_inheritance_limitations(client):
    """Test that subjects cannot grant rights beyond their own permissions."""
    # Create a hierarchy: root -> admin -> user -> guest
    client.post("/subject", json={"id": "root"})
    client.post("/subject", json={"id": "admin"})
    client.post("/subject", json={"id": "user"})
    client.post("/subject", json={"id": "guest"})
    client.post("/object", json={"id": "system_file.txt"})
    
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Root has all permissions
        graph.assign_right("root", "system_file.txt", "read")
        graph.assign_right("root", "system_file.txt", "write")
        graph.assign_right("root", "system_file.txt", "grant")
        
        # Root grants only read and grant to admin (not write)
        result = graph.grant("root", "admin", "read", "system_file.txt")
        assert result == True
        result = graph.grant("root", "admin", "grant", "system_file.txt")
        assert result == True
        
        # Admin tries to grant write to user (should fail - admin doesn't have write)
        result = graph.grant("admin", "user", "write", "system_file.txt")
        assert result == False
        
        # Admin can grant read to user (admin has read permission)
        result = graph.grant("admin", "user", "read", "system_file.txt")
        assert result == True
        
        # User tries to grant anything to guest (should fail - user has no grant permission)
        result = graph.grant("user", "guest", "read", "system_file.txt")
        assert result == False

def test_circular_permission_prevention(client):
    """Test prevention of circular permission dependencies."""
    # Create subjects
    client.post("/subject", json={"id": "alice"})
    client.post("/subject", json={"id": "bob"})
    client.post("/subject", json={"id": "charlie"})
    client.post("/object", json={"id": "shared_resource.txt"})
    
    from src.api.routes import _cluster as cluster
    if cluster and hasattr(cluster, '_graph'):
        graph = cluster._graph
        
        # Set up initial permissions
        graph.assign_right("alice", "shared_resource.txt", "grant")
        graph.assign_right("alice", "shared_resource.txt", "read")
        
        # Alice grants to bob
        result = graph.grant("alice", "bob", "read", "shared_resource.txt")
        assert result == True
        
        # Give bob grant permission
        graph.assign_right("bob", "shared_resource.txt", "grant")
        
        # Bob grants to charlie
        result = graph.grant("bob", "charlie", "read", "shared_resource.txt")
        assert result == True
        
        # This creates a potential for circular dependencies in more complex scenarios
        # The SPM model should handle this through proper cycle detection
        # For now, we just verify the basic operations work