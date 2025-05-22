#!/bin/bash

set -e

echo "🧹 Cleaning up previous containers and network..."
docker rm -f node1 node2 node3 2>/dev/null || true
docker network rm rac-nas-net 2>/dev/null || true

echo "📦 Building Docker image..."
docker build -t rac-nas:latest .

echo "🌐 Creating Docker network..."
docker network create rac-nas-net

echo "🚀 Starting 3 RAC-NAS nodes..."
for n in 1 2 3; do
  self="node${n}:4321"
  partners=$(comm -13 <(echo $n) <(seq 3) | xargs -I{} echo -n "node{}:4321," | sed 's/,$//')

  docker run -d --name "node${n}" --network rac-nas-net \
    -e SELF_ADDR="$self" -e PARTNERS="$partners" \
    -p "500${n}:5000" rac-nas:latest
done

echo "⏳ Waiting for nodes to initialize..."
sleep 5

echo "📤 Creating subject 'alice' on node1..."
curl -s -X POST http://localhost:5001/subject \
  -H 'Content-Type: application/json' \
  -d '{"id": "alice"}' | jq .

echo "🔄 Verifying graph replication across nodes:"
for n in 1 2 3; do
  echo "Node $n:"
  curl -s http://localhost:500${n}/graph | jq .
done
