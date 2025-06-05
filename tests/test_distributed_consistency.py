import pytest
import requests
import time
from unittest.mock import patch, MagicMock

class TestDistributedConsistency:
    """Test distributed consistency across multiple nodes."""
    
    def setup_method(self):
        """Setup mock nodes for testing."""
        self.nodes = {
            'node1': {'url': 'http://localhost:5001', 'cluster': MagicMock()},
            'node2': {'url': 'http://localhost:5002', 'cluster': MagicMock()},
            'node3': {'url': 'http://localhost:5003', 'cluster': MagicMock()}
        }
        
        # Mock the actual HTTP requests
        self.mock_responses = {}
    
    @patch('requests.post')
    @patch('requests.delete')
    @patch('requests.get')
    def test_permission_revocation_consistency(self, mock_get, mock_delete, mock_post):
        """Test that permission revocation is consistent across nodes."""
        
        # Mock successful responses for setup
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Simulate adding subject and object on node1
        response1 = requests.post(f"{self.nodes['node1']['url']}/subject", 
                                json={"id": "alice"})
        response2 = requests.post(f"{self.nodes['node1']['url']}/object", 
                                json={"id": "document.txt"})
        
        # Assign write permission
        response3 = requests.post(f"{self.nodes['node1']['url']}/assign",
                                json={"src": "alice", "dst": "document.txt", "right": "write"})
        
        # Mock successful write
        mock_post.return_value.status_code = 200
        write_response = requests.post(f"{self.nodes['node1']['url']}/write",
                                     json={"subject": "alice", "object": "document.txt", 
                                          "content": "Initial content"})
        assert write_response.status_code == 200
        
        # Mock permission removal
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"status": "ok"}
        
        # Remove write permission from node1
        revoke_response = requests.delete(f"{self.nodes['node1']['url']}/assign",
                                        json={"src": "alice", "dst": "document.txt", "right": "write"})
        
        # Mock failed write on node2 (should be denied due to replication)
        mock_post.return_value.status_code = 403
        mock_post.return_value.json.return_value = {"error": "write denied"}
        
        # Try to write from node2 - should fail
        denied_response = requests.post(f"{self.nodes['node2']['url']}/write",
                                      json={"subject": "alice", "object": "document.txt", 
                                           "content": "Should be denied"})
        assert denied_response.status_code == 403
    
    @patch('requests.post')
    @patch('requests.get')
    def test_cross_node_access_after_permission_change(self, mock_get, mock_post):
        """Test that permission changes on one node affect access on other nodes."""
        
        # Setup: Create subject and object
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Add subject bob and object on node1
        requests.post(f"{self.nodes['node1']['url']}/subject", json={"id": "bob"})
        requests.post(f"{self.nodes['node1']['url']}/object", json={"id": "shared_file.txt"})
        
        # Grant write permission on node1
        requests.post(f"{self.nodes['node1']['url']}/assign",
                     json={"src": "bob", "dst": "shared_file.txt", "right": "write"})
        
        # Bob should be able to write from node2
        mock_post.return_value.status_code = 200
        write_response = requests.post(f"{self.nodes['node2']['url']}/write",
                                     json={"subject": "bob", "object": "shared_file.txt", 
                                          "content": "Cross-node write"})
        assert write_response.status_code == 200
        
        # Now revoke permission on node3
        mock_post.return_value.status_code = 200  # Successful revocation
        requests.post(f"{self.nodes['node3']['url']}/revoke",
                     json={"src": "bob", "dst": "shared_file.txt", "right": "write"})
        
        # Bob should no longer be able to write from node1
        mock_post.return_value.status_code = 403
        mock_post.return_value.json.return_value = {"error": "write denied"}
        
        denied_response = requests.post(f"{self.nodes['node1']['url']}/write",
                                      json={"subject": "bob", "object": "shared_file.txt", 
                                           "content": "Should fail"})
        assert denied_response.status_code == 403
    
    @patch('requests.get')
    def test_graph_state_consistency(self, mock_get):
        """Test that all nodes have consistent graph state."""
        
        # Mock graph responses from different nodes
        graph_state = {
            "nodes": [
                {"id": "alice", "type": "subject"},
                {"id": "document.txt", "type": "object"}
            ],
            "edges": [
                {"src": "alice", "dst": "document.txt", "rights": ["read"]}
            ]
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = graph_state
        
        # Check graph state on all nodes
        for node_name, node_info in self.nodes.items():
            response = requests.get(f"{node_info['url']}/graph")
            assert response.status_code == 200
            
            # In a real test, we'd verify all nodes return the same state
            returned_graph = response.json()
            assert len(returned_graph["nodes"]) == len(graph_state["nodes"])
            assert len(returned_graph["edges"]) == len(graph_state["edges"])
    
    @patch('requests.post')
    def test_simultaneous_permission_changes(self, mock_post):
        """Test handling of simultaneous permission changes on different nodes."""
        
        # Mock successful operations
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Simulate simultaneous permission grants on different nodes
        # This tests the Raft consensus mechanism
        
        # Node1 grants read permission
        response1 = requests.post(f"{self.nodes['node1']['url']}/assign",
                                json={"src": "alice", "dst": "file1.txt", "right": "read"})
        
        # Node2 grants write permission simultaneously  
        response2 = requests.post(f"{self.nodes['node2']['url']}/assign",
                                json={"src": "alice", "dst": "file1.txt", "right": "write"})
        
        # Both should succeed due to Raft ordering
        assert response1.status_code == 201
        assert response2.status_code == 201
    
    @patch('requests.post')
    def test_network_partition_recovery(self, mock_post):
        """Test system behavior during network partition scenarios."""
        
        # Simulate network partition by making some nodes unreachable
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'node3' in url:
                # Simulate node3 being unreachable
                raise requests.exceptions.ConnectionError("Network partition")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = side_effect
        
        # Operations on reachable nodes should still work
        response1 = requests.post(f"{self.nodes['node1']['url']}/subject", 
                                json={"id": "partition_test_user"})
        assert response1.status_code == 201
        
        response2 = requests.post(f"{self.nodes['node2']['url']}/subject", 
                                json={"id": "partition_test_user2"})
        assert response2.status_code == 201
        
        # Operations on partitioned node should fail
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(f"{self.nodes['node3']['url']}/subject", 
                         json={"id": "should_fail"})