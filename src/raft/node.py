# src/raft/node.py

"""
    Summary of the module:
    - This module sets up a Raft node using the raftos library.
        - Raft is a consensus algorithm used for distributed systems to ensure that multiple nodes agree on the same state.
    - The module defines a function `setup_raft` that initializes the Raft node with a specified node ID and a list of peer IDs.
    - It configures the Raft node with a serializer and a callback for when the node becomes the leader.
    - The node ID and peer IDs are passed as arguments to the setup function.
    - The Raft node is registered with a specified address and cluster of peers.
    - The module uses asyncio for asynchronous tasks and environment variables for configuration.
"""

import asyncio, raftos, os

def setup_raft(node_id: str, peer_ids: list[str]) -> None:
    raft_port = int(os.getenv("RAFT_PORT", "10000"))
    peers = [f"{peer}:{raft_port}" for peer in peer_ids]

    raftos.configure(
        {
            "serializer": raftos.serializers.JSONSerializer,
            "on_leader": lambda: print(f"[{node_id}] 🗳️  I’m the leader"),
        }
    )

    loop = asyncio.get_event_loop()
    loop.create_task(
        raftos.register(node_id, cluster=peers, address=f"0.0.0.0:{raft_port}")
    )

    print(f"[{node_id}] Raft node up on 0.0.0.0:{raft_port}, peers: {peers}")
