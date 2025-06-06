#!/bin/bash
# Test script for Raspberry Pi cluster functionality

set -e

echo "🧪 Testing Raspberry Pi Cluster Functionality"
echo "============================================="

if [ ! -f "rpi_cluster.json" ]; then
    echo "❌ Configuration file rpi_cluster.json not found!"
    echo "   Run setup_rpi_cluster.sh first."
    exit 1
fi

# Parse first node from config for testing
FIRST_NODE_IP=$(python3 -c "
import json
with open('rpi_cluster.json') as f:
    config = json.load(f)
    first_node = list(config['nodes'].values())[0]
    print(first_node['ip'])
")

API_PORT=$(python3 -c "
import json
with open('rpi_cluster.json') as f:
    config = json.load(f)
    first_node = list(config['nodes'].values())[0]
    print(first_node.get('api_port', 5000))
")

BASE_URL="http://${FIRST_NODE_IP}:${API_PORT}"

echo "🌐 Testing API endpoint: $BASE_URL"

echo "📤 Creating test subjects..."
curl -s -X POST "${BASE_URL}/subject" \
     -H 'Content-Type: application/json' \
     -d '{"id": "alice"}' > /dev/null

curl -s -X POST "${BASE_URL}/subject" \
     -H 'Content-Type: application/json' \
     -d '{"id": "bob"}' > /dev/null

echo "📁 Creating test object..."
curl -s -X POST "${BASE_URL}/object" \
     -H 'Content-Type: application/json' \
     -d '{"id": "test_document.txt"}' > /dev/null

echo "🔐 Assigning rights..."
curl -s -X POST "${BASE_URL}/assign" \
     -H 'Content-Type: application/json' \
     -d '{"src": "alice", "dst": "test_document.txt", "right": "write"}' > /dev/null

echo "✍️  Testing file write..."
curl -s -X POST "${BASE_URL}/write" \
     -H 'Content-Type: application/json' \
     -d '{"subject": "alice", "object": "test_document.txt", "content": "Hello from Raspberry Pi cluster!"}'

echo ""
echo "📊 Current graph state:"
curl -s "${BASE_URL}/graph" | python3 -m json.tool

echo ""
echo "📋 Cluster status:"
python3 rpi_deployment.py --action status

echo ""
echo "✅ Test completed successfully!"