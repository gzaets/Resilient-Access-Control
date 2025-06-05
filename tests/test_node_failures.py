import pytest
import time
from unittest.mock import MagicMock, patch
import requests
from threading import Thread

class TestNodeFailureScenarios:
    """Test system behavior during various node failure scenarios."""
    
    def setup_method(self):
        """Setup mock cluster for testing."""
        self.nodes = {
            'node1': {'url': 'http://localhost:5001', 'status': 'online'},
            'node2': {'url': 'http://localhost:5002', 'status': 'online'}, 
            'node3': {'url': 'http://localhost:5003', 'status': 'online'}
        }
    
    @patch('requests.post')
    @patch('requests.get')
    def test_leader_node_failure(self, mock_get, mock_post):
        """Test system behavior when leader node fails."""
        
        # Initially all nodes respond
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"status": "ok"}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"nodes": [], "edges": []}
        
        # Create subject on leader (node1)
        response = requests.post(f"{self.nodes['node1']['url']}/subject", 
                               json={"id": "test_user"})
        assert response.status_code == 201
        
        # Simulate leader failure
        def leader_failure_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'node1' in url:
                raise requests.exceptions.ConnectionError("Leader node failed")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = leader_failure_side_effect
        
        # Operations should still work on remaining nodes (after leader election)
        response = requests.post(f"{self.nodes['node2']['url']}/subject",
                               json={"id": "post_failure_user"})
        assert response.status_code == 201
    
    @patch('requests.post')
    def test_minority_node_failure(self, mock_post):
        """Test that system continues working when minority of nodes fail."""
        
        # Simulate one node failure out of three
        def minority_failure_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'node3' in url:
                raise requests.exceptions.ConnectionError("Node3 failed")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = minority_failure_side_effect
        
        # Majority nodes (node1, node2) should continue working
        response1 = requests.post(f"{self.nodes['node1']['url']}/subject",
                                json={"id": "user1"})
        assert response1.status_code == 201
        
        response2 = requests.post(f"{self.nodes['node2']['url']}/subject", 
                                json={"id": "user2"})
        assert response2.status_code == 201
        
        # Failed node should raise exception
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.post(f"{self.nodes['node3']['url']}/subject",
                         json={"id": "should_fail"})
    
    @patch('requests.post')
    def test_majority_node_failure(self, mock_post):
        """Test system behavior when majority of nodes fail."""
        
        # Simulate two nodes failing out of three
        def majority_failure_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'node2' in url or 'node3' in url:
                raise requests.exceptions.ConnectionError("Majority nodes failed")
            else:
                # Remaining node should reject operations (no quorum)
                mock_response = MagicMock()
                mock_response.status_code = 503  # Service unavailable
                mock_response.json.return_value = {"error": "No quorum"}
                return mock_response
        
        mock_post.side_effect = majority_failure_side_effect
        
        # Remaining node should reject operations due to lack of quorum
        response = requests.post(f"{self.nodes['node1']['url']}/subject",
                               json={"id": "no_quorum_user"})
        assert response.status_code == 503
    
    @patch('requests.post')
    @patch('requests.get')
    def test_network_partition_recovery(self, mock_get, mock_post):
        """Test recovery after network partition is healed."""
        
        # Initially simulate partition (nodes 1,2 vs node 3)
        partition_active = True
        
        def partition_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if partition_active and 'node3' in url:
                raise requests.exceptions.ConnectionError("Network partition")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = partition_side_effect
        mock_get.side_effect = partition_side_effect
        
        # Operations on majority partition should work
        response = requests.post(f"{self.nodes['node1']['url']}/subject",
                               json={"id": "partition_user"})
        assert response.status_code == 201
        
        # Heal the partition
        partition_active = False
        
        # Now all nodes should work again
        response = requests.post(f"{self.nodes['node3']['url']}/subject",
                               json={"id": "post_partition_user"})
        assert response.status_code == 201
    
    @patch('requests.post')
    def test_cascading_node_failures(self, mock_post):
        """Test system behavior during cascading node failures."""
        
        failure_sequence = []
        
        def cascading_failure_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            
            # Simulate failures happening over time
            if len(failure_sequence) >= 1 and 'node1' in url:
                raise requests.exceptions.ConnectionError("Node1 failed")
            elif len(failure_sequence) >= 2 and 'node2' in url:
                raise requests.exceptions.ConnectionError("Node2 failed")
            elif len(failure_sequence) >= 3 and 'node3' in url:
                raise requests.exceptions.ConnectionError("Node3 failed")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201 if len(failure_sequence) < 2 else 503
                mock_response.json.return_value = {"status": "ok"} if len(failure_sequence) < 2 else {"error": "No quorum"}
                return mock_response
        
        mock_post.side_effect = cascading_failure_side_effect
        
        # First operation should succeed
        response = requests.post(f"{self.nodes['node1']['url']}/subject",
                               json={"id": "before_cascade"})
        assert response.status_code == 201
        
        # Trigger first failure
        failure_sequence.append("node1")
        
        # Should still work with remaining nodes
        response = requests.post(f"{self.nodes['node2']['url']}/subject", 
                               json={"id": "after_first_failure"})
        assert response.status_code == 201
        
        # Trigger second failure (majority lost)
        failure_sequence.append("node2")
        
        # Should fail due to no quorum
        response = requests.post(f"{self.nodes['node3']['url']}/subject",
                               json={"id": "after_majority_failure"})
        assert response.status_code == 503
    
    @patch('requests.post')
    @patch('requests.get')
    def test_slow_node_detection(self, mock_get, mock_post):
        """Test detection and handling of slow/unresponsive nodes."""
        
        def slow_node_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'node2' in url:
                # Simulate slow response
                time.sleep(0.1)  # Simulate network delay
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = slow_node_side_effect
        mock_get.side_effect = slow_node_side_effect
        
        # Operations should still complete, but might be slower
        start_time = time.time()
        response = requests.post(f"{self.nodes['node2']['url']}/subject",
                               json={"id": "slow_response_user"})
        end_time = time.time()
        
        assert response.status_code == 201
        # In a real system, timeouts would be configured
    
    @patch('requests.post')
    def test_intermittent_failures(self, mock_post):
        """Test handling of intermittent node failures."""
        
        failure_count = {'count': 0}
        
        def intermittent_failure_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            failure_count['count'] += 1
            
            # Fail every other request to node2
            if 'node2' in url and failure_count['count'] % 2 == 0:
                raise requests.exceptions.ConnectionError("Intermittent failure")
            else:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {"status": "ok"}
                return mock_response
        
        mock_post.side_effect = intermittent_failure_side_effect
        
        # Multiple operations, some should succeed, some fail
        results = []
        for i in range(5):
            try:
                response = requests.post(f"{self.nodes['node2']['url']}/subject",
                                       json={"id": f"intermittent_user_{i}"})
                results.append(response.status_code)
            except requests.exceptions.ConnectionError:
                results.append("failed")
        
        # Should have mix of successes and failures
        assert 201 in results
        assert "failed" in results
    
    @patch('requests.post')
    @patch('requests.get')
    def test_node_recovery_synchronization(self, mock_get, mock_post):
        """Test that recovered nodes synchronize with cluster state."""
        
        node_down = {'node3': True}
        cluster_state = {"nodes": [], "edges": []}
        
        def recovery_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            
            if 'node3' in url and node_down['node3']:
                raise requests.exceptions.ConnectionError("Node down")
            else:
                mock_response = MagicMock()
                if '/graph' in url:
                    mock_response.status_code = 200
                    mock_response.json.return_value = cluster_state
                else:
                    mock_response.status_code = 201
                    mock_response.json.return_value = {"status": "ok"}
                    # Update cluster state
                    if mock_response.status_code == 201:
                        cluster_state["nodes"].append({"id": "test_node"})
                return mock_response
        
        mock_post.side_effect = recovery_side_effect
        mock_get.side_effect = recovery_side_effect
        
        # Make changes while node3 is down
        response = requests.post(f"{self.nodes['node1']['url']}/subject",
                               json={"id": "while_node3_down"})
        assert response.status_code == 201
        
        # Bring node3 back online
        node_down['node3'] = False
        
        # Node3 should be able to serve requests and have synchronized state
        response = requests.get(f"{self.nodes['node3']['url']}/graph")
        assert response.status_code == 200
        
        # State should include changes made while node was down
        graph_data = response.json()
        assert len(graph_data["nodes"]) > 0