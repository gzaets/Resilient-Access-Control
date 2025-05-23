import pytest
from src.core.spm import SPMGraph

def test_add_and_delete_subject():
    graph = SPMGraph()
    graph.add_subject("alice")
    assert "alice" in graph.g.nodes
    assert graph.g.nodes["alice"]["type"] == "subject"

    graph.delete_subject("alice")
    assert "alice" not in graph.g.nodes

def test_add_and_delete_object():
    graph = SPMGraph()
    graph.add_object("file1")
    assert "file1" in graph.g.nodes
    assert graph.g.nodes["file1"]["type"] == "object"

    graph.delete_object("file1")
    assert "file1" not in graph.g.nodes

def test_assign_right():
    graph = SPMGraph()
    graph.add_subject("alice")
    graph.add_object("file1")
    assert graph.assign_right("alice", "file1", "read") is True
    assert graph.has_right("alice", "file1", "read") is True

def test_invalid_right_assignment():
    graph = SPMGraph()
    graph.add_subject("alice")
    graph.add_object("file1")
    assert graph.assign_right("alice", "file1", "invalid_right") is False
