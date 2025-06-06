#!/bin/bash
# Quick setup script for Raspberry Pi cluster deployment

set -e

echo "🍓 RAC-NAS Raspberry Pi Cluster Setup"
echo "====================================="

# Check if configuration exists
if [ ! -f "rpi_cluster.json" ]; then
    echo "📝 Creating sample configuration..."
    python3 rpi_deployment.py --action deploy --config rpi_cluster.json 2>/dev/null || true
    echo ""
    echo "⚠️  Please edit rpi_cluster.json with your Raspberry Pi IP addresses and settings"
    echo "   Then run this script again."
    exit 1
fi

echo "🔧 Installing local dependencies..."
pip3 install -r requirements-rpi.txt

echo "🚀 Deploying to Raspberry Pi cluster..."
python3 rpi_deployment.py --action deploy

echo "▶️  Starting cluster..."
python3 rpi_deployment.py --action start-cluster

echo "🧪 Running cluster tests..."
python3 rpi_deployment.py --action test

echo ""
echo "🎉 Setup complete! Your Raspberry Pi cluster is ready."
echo ""
echo "💡 Useful commands:"
echo "   Check status:  python3 rpi_deployment.py --action status"
echo "   Stop cluster:  python3 rpi_deployment.py --action stop-cluster"
echo "   Run tests:     python3 rpi_deployment.py --action test"