#!/bin/bash
set -e

echo "📤 Creating subjects 'bob', 'alice', and 'admin'..."
curl -s -X POST http://localhost:5001/subject -H 'Content-Type: application/json' -d '{"id": "bob"}' > /dev/null
curl -s -X POST http://localhost:5001/subject -H 'Content-Type: application/json' -d '{"id": "alice"}' > /dev/null
curl -s -X POST http://localhost:5001/subject -H 'Content-Type: application/json' -d '{"id": "admin"}' > /dev/null

echo "📁 Creating object 't1.txt'..."
curl -s -X POST http://localhost:5001/object -H 'Content-Type: application/json' -d '{"id": "t1.txt"}' > /dev/null

echo "🔐 Assigning 'write' from admin to bob..."
curl -s -X POST http://localhost:5001/assign \
     -H 'Content-Type: application/json' \
     -d '{"src": "admin", "dst": "t1.txt", "right": "write"}' > /dev/null

curl -s -X POST http://localhost:5001/assign \
     -H 'Content-Type: application/json' \
     -d '{"src": "bob", "dst": "t1.txt", "right": "write"}' > /dev/null

echo "✍️ Writing to 't1.txt' as bob (should succeed)..."
curl -s -X POST http://localhost:5001/write \
     -H 'Content-Type: application/json' \
     -d '{"subject": "bob", "object": "t1.txt", "content": "Bob was here!"}'

echo "🚫 Attempting to write as alice (should fail)..."
response=$(curl -s -X POST http://localhost:5001/write \
     -H 'Content-Type: application/json' \
     -d '{"subject": "alice", "object": "t1.txt", "content": "Alice tries!"}')

if echo "$response" | grep -q "write denied"; then
  echo "✅ Access denied correctly for alice."
else
  echo "❌ Alice was able to write without permission!"
  echo "Response: $response"
  exit 1
fi

echo "📥 Final graph:"
curl -s http://localhost:5001/graph 
# | jq .

echo "📄 File contents (on node1):"
docker exec -it node1 cat storage/t1.txt