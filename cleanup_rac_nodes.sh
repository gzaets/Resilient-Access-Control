#!/bin/bash

echo "🛑 Stopping and removing nodes..."
docker rm -f node1 node2 node3 2>/dev/null || true

echo "🌐 Removing Docker network..."
docker network rm rac-nas-net 2>/dev/null || true

# Optional: Clean up unused Docker resources (only if you want this)
# echo "🧽 Pruning unused Docker resources..."
# docker system prune -f

echo "✅ RAC-NAS cluster cleanup complete."
