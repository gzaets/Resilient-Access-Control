# src/raft/node.py
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
