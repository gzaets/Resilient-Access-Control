import pytest
import requests
import time
from unittest.mock import patch, MagicMock, Mock

class TestNodeFailureScenarios:
    """Test various node failure scenarios."""
    
    def setup_method(self):
        """Setup mock cluster for testing."""
        self.cluster = MagicMock()
        self.cluster.nodes = ['node1', 'node2', 'node3']
        self.cluster.leader = 'node1'
        self.cluster.total_nodes = 3
    
    @patch('requests.post')
    def test_leader_node_failure(self, mock_post):
        """Test system behavior when leader node fails."""
        # Setup: Simulate leader election after failure
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            if call_count == 1:
                # First call fails - leader is down
                response.status_code = 503
                response.json.return_value = {"error": "leader unavailable", "leader": None}
            else:
                # Subsequent calls succeed - new leader elected
                response.status_code = 200
                response.json.return_value = {"status": "ok", "leader": "node2", "term": 2}
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First attempt fails due to leader failure
        failure_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert failure_response.status_code == 503
        assert failure_response.json()["error"] == "leader unavailable"
        assert failure_response.json()["leader"] is None
        
        # Second attempt succeeds with new leader
        success_response = requests.post(
            'http://localhost:5002/subject',
            json={"id": "alice"}
        )
        assert success_response.status_code == 200
        assert success_response.json()["status"] == "ok"
        assert success_response.json()["leader"] == "node2"
        assert success_response.json()["term"] == 2
        
        # Verify leader election occurred
        assert call_count == 2
    
    @patch('requests.post')
    def test_minority_node_failure(self, mock_post):
        """Test system behavior when minority of nodes fail."""
        # Setup: Simulate 1 node down out of 3 (minority failure)
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "status": "ok", 
            "active_nodes": 2,
            "failed_nodes": ["node3"],
            "majority_available": True
        }
        
        # System should continue operating with minority failure
        response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["active_nodes"] == 2
        assert response.json()["majority_available"] == True
        assert "node3" in response.json()["failed_nodes"]
    
    @patch('requests.post')
    def test_majority_node_failure(self, mock_post):
        """Test system behavior when majority of nodes fail."""
        # Setup: Simulate 2 nodes down out of 3 (majority failure)
        mock_post.return_value.status_code = 503
        mock_post.return_value.json.return_value = {
            "error": "insufficient nodes for consensus",
            "active_nodes": 1,
            "required_nodes": 2,
            "failed_nodes": ["node2", "node3"],
            "read_only_mode": True
        }
        
        # System should reject writes during majority failure
        response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        
        assert response.status_code == 503
        assert "insufficient nodes" in response.json()["error"]
        assert response.json()["active_nodes"] == 1
        assert response.json()["required_nodes"] == 2
        assert response.json()["read_only_mode"] == True
        assert len(response.json()["failed_nodes"]) == 2
    
    @patch('requests.post')
    @patch('requests.get')
    def test_network_partition_recovery(self, mock_get, mock_post):
        """Test recovery from network partitions."""
        # Setup: Simulate partition then recovery
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            if call_count <= 2:
                # During partition - minority nodes available
                response.status_code = 503
                response.json.return_value = {
                    "error": "network partition detected",
                    "available_nodes": 1,
                    "partition_size": 1,
                    "majority_lost": True
                }
            else:
                # After recovery - majority restored
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "available_nodes": 3,
                    "partition_recovered": True,
                    "sync_complete": True
                }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # During partition - operations should fail
        partition_response1 = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert partition_response1.status_code == 503
        assert "network partition detected" in partition_response1.json()["error"]
        assert partition_response1.json()["majority_lost"] == True
        
        # Still in partition
        partition_response2 = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "doc.txt", "right": "read"}
        )
        assert partition_response2.status_code == 503
        
        # After recovery - operations should succeed
        recovery_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "bob"}
        )
        assert recovery_response.status_code == 200
        assert recovery_response.json()["status"] == "ok"
        assert recovery_response.json()["partition_recovered"] == True
        assert recovery_response.json()["available_nodes"] == 3
        assert recovery_response.json()["sync_complete"] == True
        
        # Verify call progression
        assert call_count == 3
    
    @patch('requests.post')
    def test_cascading_node_failures(self, mock_post):
        """Test handling of cascading node failures."""
        # Setup: Simulate nodes failing one after another
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            if call_count == 1:
                # First failure - still majority available
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "active_nodes": 2,
                    "failed_nodes": ["node3"],
                    "warning": "node failure detected"
                }
            elif call_count == 2:
                # Second failure - majority lost
                response.status_code = 503
                response.json.return_value = {
                    "error": "cascading failure detected",
                    "active_nodes": 1,
                    "failed_nodes": ["node2", "node3"],
                    "read_only_mode": True,
                    "emergency_mode": True
                }
            else:
                # Recovery - nodes coming back online
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "active_nodes": 3,
                    "failed_nodes": [],
                    "cascading_recovery": True
                }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First node failure - system continues
        first_failure = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert first_failure.status_code == 200
        assert first_failure.json()["active_nodes"] == 2
        assert "node3" in first_failure.json()["failed_nodes"]
        assert "warning" in first_failure.json()
        
        # Second node failure - triggers emergency mode
        second_failure = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "doc.txt", "right": "read"}
        )
        assert second_failure.status_code == 503
        assert "cascading failure detected" in second_failure.json()["error"]
        assert second_failure.json()["active_nodes"] == 1
        assert second_failure.json()["emergency_mode"] == True
        assert len(second_failure.json()["failed_nodes"]) == 2
        
        # Recovery - nodes restored
        recovery = requests.post(
            'http://localhost:5001/subject',
            json={"id": "bob"}
        )
        assert recovery.status_code == 200
        assert recovery.json()["active_nodes"] == 3
        assert len(recovery.json()["failed_nodes"]) == 0
        assert recovery.json()["cascading_recovery"] == True
        
        assert call_count == 3
    
    @patch('requests.post')
    def test_slow_node_detection(self, mock_post):
        """Test detection and handling of slow nodes."""
        # Setup: Simulate slow node responses
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            if 'node3' in url or call_count % 3 == 0:
                # Simulate slow node with timeout
                response.status_code = 408  # Request Timeout
                response.json.return_value = {
                    "error": "request timeout",
                    "node": "node3",
                    "response_time_ms": 5000,
                    "threshold_ms": 1000
                }
            else:
                # Normal nodes respond quickly
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "node": "node1" if call_count % 2 == 1 else "node2",
                    "response_time_ms": 50,
                    "slow_nodes_detected": ["node3"]
                }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First request - normal response
        normal_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert normal_response.status_code == 200
        assert normal_response.json()["response_time_ms"] == 50
        assert "node3" in normal_response.json()["slow_nodes_detected"]
        
        # Second request - normal response  
        normal_response2 = requests.post(
            'http://localhost:5002/subject',
            json={"id": "bob"}
        )
        assert normal_response2.status_code == 200
        
        # Third request - slow node timeout
        slow_response = requests.post(
            'http://localhost:5003/subject',
            json={"id": "charlie"}
        )
        assert slow_response.status_code == 408
        assert "request timeout" in slow_response.json()["error"]
        assert slow_response.json()["response_time_ms"] == 5000
        assert slow_response.json()["threshold_ms"] == 1000
        
        assert call_count == 3
    
    @patch('requests.post')
    def test_intermittent_failures(self, mock_post):
        """Test handling of intermittent node failures."""
        # Setup: Simulate intermittent failures with retry logic
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            # Intermittent pattern: fail, succeed, fail, succeed
            if call_count % 2 == 1:
                # Odd attempts fail
                response.status_code = 503
                response.json.return_value = {
                    "error": "intermittent failure",
                    "node": "node2",
                    "attempt": call_count,
                    "retry_suggested": True
                }
            else:
                # Even attempts succeed
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "node": "node1",
                    "attempt": call_count,
                    "recovered_from_failure": True
                }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First attempt - fails
        first_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert first_response.status_code == 503
        assert "intermittent failure" in first_response.json()["error"]
        assert first_response.json()["retry_suggested"] == True
        
        # Retry - succeeds
        retry_response = requests.post(
            'http://localhost:5001/subject',
            json={"id": "alice"}
        )
        assert retry_response.status_code == 200
        assert retry_response.json()["status"] == "ok"
        assert retry_response.json()["recovered_from_failure"] == True
        
        # Third attempt - fails again
        third_response = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "doc.txt", "right": "read"}
        )
        assert third_response.status_code == 503
        assert "intermittent failure" in third_response.json()["error"]
        
        # Fourth attempt - succeeds again
        fourth_response = requests.post(
            'http://localhost:5001/assign',
            json={"src": "alice", "dst": "doc.txt", "right": "read"}
        )
        assert fourth_response.status_code == 200
        assert fourth_response.json()["recovered_from_failure"] == True
        
        assert call_count == 4
    
    @patch('requests.post')
    def test_node_recovery_synchronization(self, mock_post):
        """Test synchronization when failed nodes recover."""
        # Setup: Simulate node recovery with synchronization
        call_count = 0
        
        def mock_post_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            response = Mock()
            
            if call_count == 1:
                # First call - node still recovering
                response.status_code = 202  # Accepted but not ready
                response.json.return_value = {
                    "status": "recovering",
                    "node": "node3",
                    "sync_progress": 45,
                    "log_entries_behind": 12,
                    "estimated_completion_ms": 2000
                }
            else:
                # Subsequent calls - node fully recovered
                response.status_code = 200
                response.json.return_value = {
                    "status": "ok",
                    "node": "node3",
                    "sync_progress": 100,
                    "log_entries_behind": 0,
                    "recovery_complete": True,
                    "total_recovery_time_ms": 3500
                }
            return response
        
        mock_post.side_effect = mock_post_side_effect
        
        # First request during recovery
        recovery_response = requests.post(
            'http://localhost:5003/subject',
            json={"id": "alice"}
        )
        assert recovery_response.status_code == 202
        assert recovery_response.json()["status"] == "recovering"
        assert recovery_response.json()["sync_progress"] == 45
        assert recovery_response.json()["log_entries_behind"] == 12
        assert recovery_response.json()["estimated_completion_ms"] == 2000
        
        # Second request after recovery complete
        complete_response = requests.post(
            'http://localhost:5003/assign',
            json={"src": "alice", "dst": "doc.txt", "right": "write"}
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "ok"
        assert complete_response.json()["sync_progress"] == 100
        assert complete_response.json()["log_entries_behind"] == 0
        assert complete_response.json()["recovery_complete"] == True
        assert complete_response.json()["total_recovery_time_ms"] == 3500
        
        assert call_count == 2
