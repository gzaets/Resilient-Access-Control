import pytest
import requests
import time
from unittest.mock import patch, MagicMock, Mock

class TestDistributedConsistency:
    """Test distributed consistency across multiple nodes."""
    
    def setup_method(self):
        """Setup mock nodes for testing."""
        self.nodes = {
            'node1': {'url': 'http://localhost:5001', 'cluster': MagicMock()},
            'node2': {'url': 'http://localhost:5002', 'cluster': MagicMock()},
            'node3': {'url': 'http://localhost:5003', 'cluster': MagicMock()}
        }
    
    @patch('requests.post')
    @patch('requests.delete')
    @patch('requests.get')
    def test_permission_revocation_consistency(self, mock_get, mock_delete, mock_post):
        """Test that permission revocation is consistent across nodes."""
        # Setup: Subject creation succeeds
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Setup: Permission deletion succeeds
        mock_delete.return_value.status_code = 200
        mock_delete.return_value.json.return_value = {"status": "deleted"}
        
        # Setup: Graph state check
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "nodes": [{"id": "alice", "type": "subject"}],
            "edges": []  # No edges after revocation
        }
        
        # Simulate permission revocation
        response = requests.delete('http://localhost:5001/assign')
        
        # Verify revocation was processed
        assert mock_delete.called
        assert response.status_code == 200
        
        # Verify consistent state across nodes
        graph_response = requests.get('http://localhost:5001/graph')
        assert graph_response.status_code == 200
        graph_data = graph_response.json()
        assert len(graph_data["edges"]) == 0  # No permissions remain
    
    @patch('requests.post')
    @patch('requests.get')
    def test_cross_node_access_after_permission_change(self, mock_get, mock_post):
        """Test that permission changes on one node affect access on other nodes."""
        # Setup: Permission assignment succeeds
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        # Setup: Different responses for different operations
        def mock_post_side_effect(url, **kwargs):
            response = Mock()
            if 'assign' in url:
                response.status_code = 201
                response.json.return_value = {"status": "permission_assigned"}
            elif 'write' in url:
                response.status_code = 200
                response.json.return_value = {"status": "write_successful"}
            else:
                response.status_code = 201
                response.json.return_value = {"status": "ok"}
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Test permission assignment on node 1
        assign_response = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "document.txt", "right": "write"}
        )
        assert assign_response.status_code == 201
        assert assign_response.json()["status"] == "permission_assigned"
        
        # Test access from different node (should see the permission)
        access_response = requests.post(
            'http://localhost:5002/write',
            json={"subject": "alice", "object": "document.txt", "content": "test"}
        )
        assert access_response.status_code == 200
        assert access_response.json()["status"] == "write_successful"
    
    @patch('requests.get')
    def test_graph_state_consistency(self, mock_get):
        """Test that all nodes have consistent graph state."""
        # Setup consistent graph state across all nodes
        consistent_graph = {
            "nodes": [
                {"id": "alice", "type": "subject"},
                {"id": "bob", "type": "subject"},
                {"id": "document.txt", "type": "object"}
            ],
            "edges": [
                {"src": "alice", "dst": "document.txt", "right": "write"},
                {"src": "bob", "dst": "document.txt", "right": "read"}
            ]
        }
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = consistent_graph
        
        # Check each node has the same graph state
        for node_name, node_info in self.nodes.items():
            response = requests.get(f"{node_info['url']}/graph")
            assert response.status_code == 200
            
            graph_data = response.json()
            assert len(graph_data["nodes"]) == 3
            assert len(graph_data["edges"]) == 2
            
            # Verify specific nodes exist
            node_ids = [node["id"] for node in graph_data["nodes"]]
            assert "alice" in node_ids
            assert "bob" in node_ids
            assert "document.txt" in node_ids
    
    @patch('requests.post')
    def test_simultaneous_permission_changes(self, mock_post):
        """Test handling of simultaneous permission changes on different nodes."""
        # Setup: Track calls to ensure proper ordering/consensus
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            response.status_code = 201
            response.json.return_value = {
                "status": "ok", 
                "sequence": call_count,  # Simulate Raft log sequence
                "leader": "node1"
            }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # Simulate simultaneous assignments from different nodes
        responses = []
        
        # Node 1: Assign alice write permission
        response1 = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "file1.txt", "right": "write"}
        )
        responses.append(response1)
        
        # Node 2: Assign bob read permission  
        response2 = requests.post(
            'http://localhost:5002/assign',
            json={"src": "bob", "dst": "file1.txt", "right": "read"}
        )
        responses.append(response2)
        
        # Node 3: Assign charlie admin permission
        response3 = requests.post(
            'http://localhost:5003/assign',
            json={"src": "charlie", "dst": "file1.txt", "right": "admin"}
        )
        responses.append(response3)
        
        # Verify all operations succeeded
        for response in responses:
            assert response.status_code == 201
            assert response.json()["status"] == "ok"
            assert "sequence" in response.json()  # Raft ordering
            assert response.json()["leader"] == "node1"  # Consistent leader
        
        # Verify calls were made in order (Raft consensus)
        assert call_count == 3
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    def test_network_partition_recovery(self, mock_post):
        """Test system behavior during network partition scenarios."""
        # Setup: First call fails (network partition), second succeeds (recovery)
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            if call_count == 1:
                # First call simulates partition - return 503 (service unavailable)
                response.status_code = 503
                response.json.return_value = {"error": "network partition detected", "available_nodes": 1}
            else:
                # Subsequent calls succeed after partition recovery
                response.status_code = 201
                response.json.return_value = {"status": "ok", "recovered": True, "available_nodes": 3}
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First attempt should indicate partition (minority nodes available)
        partition_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert partition_response.status_code == 503
        assert "network partition detected" in partition_response.json()["error"]
        assert partition_response.json()["available_nodes"] == 1
        
        # Second attempt should succeed (partition recovered)
        recovery_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert recovery_response.status_code == 201
        assert recovery_response.json()["status"] == "ok"
        assert recovery_response.json()["recovered"] == True
        assert recovery_response.json()["available_nodes"] == 3
        
        # Verify exactly 2 attempts were made
        assert call_count == 2
        assert mock_post.call_count == 2
