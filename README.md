# Resilient Access Control NAS

**A Distributed NAS System with Fault-Tolerant SPM-Based Access Control**  
ECS 235B – Foundations of Computer and Information Security  
Spring 2025 – UC Davis

## Overview

This project implements a **distributed, fault-tolerant Network Attached Storage (NAS)** system that enforces **fine-grained access control policies** based on the **Schematic Protection Model (SPM)**. It is designed to run on networks of unreliable or constrained devices such as **Raspberry Pi clusters** or **Dockerized virtual nodes**.

Instead of using traditional access control matrices, this system uses a **graph-based permission model** where **subjects** (users) and **objects** (files/resources) are represented as nodes, and **edges** denote access rights (e.g., `take`, `grant`, `read`, `write`). The system supports **replicated file storage**, **decentralized access enforcement**, and **real-time permission updates** through a **Raft-based consensus protocol**.

## Goals

- 📂 Store files in a distributed NAS across multiple nodes
- 🔐 Enforce access control policies using SPM logic
- ⚙️ Synchronize permissions and state changes using Raft
- 📊 Visualize permission graphs and system evolution over time
- 🛡️ Maintain correct access control even in the face of node crashes, message delays, or network partitions

## Why This Matters

Traditional NAS systems rely on centralized access control, which can be a single point of failure. Our system:
- Enables **decentralized access control** that continues to work even if some nodes fail
- Enforces **dynamic, fine-grained policies** based on the evolving state of the system
- Supports **scalability** via graph representations instead of inefficient matrices
- Applies real-world principles from distributed systems and security research

## Features

- ✅ Distributed NAS file storage
- 🔄 Raft-based consensus for permission consistency
- 📈 Scalable, graph-based representation of access rights
- 🔧 Take/grant logic and cycle detection (SPM)
- 🖥️ Real-time visualization and state monitoring
- ⚠️ Resilience to crashes, message delays, and partitions
- 📂 Local enforcement of access on each node before file access

## System Architecture

- **Distributed Nodes (Raspberry Pi or Docker):**
  - Store files and enforce local access control
  - Maintain a local instance of the SPM graph
- **SPM Engine:**
  - Handles subject/object creation, take/grant rights, and policy enforcement
- **Consensus Layer:**
  - Uses Raft to replicate changes in rights across all nodes
- **Visualization Server:**
  - Displays graph evolution, access control propagation, and failure recovery in real-time

## Hardware Requirements

- 3–5 Raspberry Pi 3 or 4 devices (1GB+ RAM, 16GB+ microSD cards)
- Power supplies, Ethernet or Wi-Fi
- Network switch or router
- Optional: Host laptop/PC for visualization and orchestration

## Software Stack

- **Language**: Python 3.9+
- **Libraries**:
  - `networkx` – permission graph modeling
  - `flask` – REST API for SPM control
  - `asyncio`, `requests` – communication
  - `sqlite3` – optional local state persistence
  - Raft library (e.g., `py-raft` or custom)
- **Platform**: Raspberry Pi OS Lite (headless) or any lightweight Linux environment

## Setup & Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/gzaets/Resilient-Access-Control.git
cd resilient-access-control
```

### 2. Install Dependencies

Ensure you have Python 3.11+ installed. Install the required dependencies using `pip`:

```bash
pip install -r requirements-main.txt
```

### 3. Build and Run the Dockerized Nodes

To deploy the system using Docker, you can use the provided `run_rac_nodes.sh` script. This script will:

1. Clean up any existing containers and networks.
2. Build the Docker image for the application.
3. Create a custom Docker network for the nodes.
4. Start three nodes (`node1`, `node2`, `node3`) with the necessary environment variables for Raft-based communication.

Run the script:

```bash
./run_rac_nodes.sh
```

This will start three nodes and initialize the system. You can verify the state of the nodes by checking the output of the script, which will display the replicated graph state across all nodes.

### 4. Interact with the System

The system exposes a REST API for managing subjects, objects, and access rights. You can interact with the API using tools like `curl`, Postman, or any HTTP client.

#### Example API Endpoints

- **Add a Subject**  
  Add a new subject (e.g., a user) to the system:
  ```bash
  curl -X POST http://localhost:5001/subject \
       -H 'Content-Type: application/json' \
       -d '{"id": "alice"}'
  ```

- **Delete a Subject**  
  Remove a subject from the system:
  ```bash
  curl -X DELETE http://localhost:5001/subject/alice
  ```

- **Assign a Right**  
  Assign a specific right (e.g., `read`, `write`) from one subject to another:
  ```bash
  curl -X POST http://localhost:5001/assign \
       -H 'Content-Type: application/json' \
       -d '{"src": "alice", "dst": "bob", "right": "read"}'
  ```

- **View the Graph**  
  Retrieve the current state of the permission graph:
  ```bash
  curl -X GET http://localhost:5001/graph
  ```

### 5. Run Tests

The repository includes unit tests for the core functionality, API routes, distributed consistency, and node failure scenarios. To run all tests, use the provided `run_tests.sh` script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

This script will:
- Set up the environment for testing.
- Execute all tests in the `tests/` directory using `pytest`.
- Display a summary of test results.

#### Test Files

The following test files provide comprehensive coverage of system functionality:

- **`test_routes.py`** (4 tests): Tests REST API endpoints for subjects, objects, and rights
- **`test_spm.py`** (4 tests): Validates core SPMGraph functionality  
- **`test_unauthorized_access.py`** (5 tests): Ensures access control enforcement
- **`test_file_operations.py`** (7 tests): Tests file system integration and permission enforcement
- **`test_permission_inheritance.py`** (6 tests): Validates advanced permission inheritance concepts
- **`test_edge_cases.py`** (10 tests): Covers edge cases and error handling
- **`test_distributed_consistency.py`** (5 tests): Tests distributed consistency across nodes
- **`test_node_failures.py`** (8 tests): Validates resilience under node failures

**Total: 49 comprehensive tests covering all aspects of the RAC-NAS system.**

#### Test Coverage Details

- **🔐 Access Control**: Validates SPM-based permission enforcement
- **🌐 API Endpoints**: Tests all REST API functionality  
- **📂 File Operations**: Ensures file system integration works correctly
- **🔄 Distributed Logic**: Tests Raft consensus and node synchronization
- **⚠️ Edge Cases**: Handles invalid inputs, race conditions, and error scenarios
- **🛡️ Resilience**: Tests system behavior under node failures and network partitions
- **🎯 Permission Inheritance**: Advanced SPM grant/take operations

#### Example Test Run

To run a specific test file:

```bash
pytest tests/test_routes.py -v
```

To run a specific test case:

```bash
pytest tests/test_routes.py::test_add_subject -v
```

To run tests with coverage report:

```bash
pytest tests/ --cov=src --cov-report=html
```

For complete testing with detailed output, use the `run_tests.sh` script as described above.

### 6. Clean Up

To stop and remove the running nodes and network, use the `cleanup_rac_nodes.sh` script:

```bash
./cleanup_rac_nodes.sh
```

This will remove all containers and the custom Docker network created during deployment.

---

## Raspberry Pi Deployment

### Prerequisites for Raspberry Pi Cluster

Before deploying to physical Raspberry Pi devices, ensure:

- **3-5 Raspberry Pi devices** (Pi 3 or 4 recommended) running Raspbian OS
- **SSH access enabled** on all Raspberry Pis
- **Network connectivity** between all devices
- **SSH key-based authentication** set up for passwordless access

### 1. Prepare Your Raspberry Pis

On each Raspberry Pi, enable SSH and install basic dependencies:

```bash
# Enable SSH (if not already enabled)
sudo systemctl enable ssh
sudo systemctl start ssh

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip git
```

### 2. Set Up SSH Key Authentication

From your control machine (laptop/PC), set up SSH keys:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy public key to each Raspberry Pi
ssh-copy-id pi@192.168.1.101  # Replace with actual IP
ssh-copy-id pi@192.168.1.102
ssh-copy-id pi@192.168.1.103
```

### 3. Configure the Cluster

Install Python dependencies on each Raspberry Pi:

```bash
# On each Raspberry Pi, install required packages
pip3 install flask networkx pysyncobj requests pytest

# Or install from requirements if available
pip3 install -r requirements.txt
```

Create a cluster configuration file on your control machine:

```bash
# Create cluster configuration
nano rpi_cluster_config.json
```

Example `rpi_cluster_config.json`:
```json
{
  "nodes": [
    {
      "id": "rpi-node-1",
      "ip": "192.168.1.101",
      "port": 4321,
      "api_port": 5001,
      "role": "leader"
    },
    {
      "id": "rpi-node-2", 
      "ip": "192.168.1.102",
      "port": 4321,
      "api_port": 5002,
      "role": "follower"
    },
    {
      "id": "rpi-node-3",
      "ip": "192.168.1.103", 
      "port": 4321,
      "api_port": 5003,
      "role": "follower"
    }
  ],
  "username": "pi",
  "ssh_key_path": "~/.ssh/id_rsa",
  "project_path": "/home/pi/Resilient-Access-Control"
}
```

### 4. Deploy to Raspberry Pi Cluster

Create a deployment script to copy files and start the system:

```bash
#!/bin/bash
# deploy_to_rpi.sh

# Configuration
NODES=("192.168.1.101" "192.168.1.102" "192.168.1.103")
USERNAME="pi"
PROJECT_DIR="/home/pi/Resilient-Access-Control"

echo "🚀 Deploying RAC-NAS to Raspberry Pi Cluster"
echo "=============================================="

# Copy project files to each node
for i in "${!NODES[@]}"; do
    NODE=${NODES[$i]}
    echo "📦 Deploying to node $((i+1)): $NODE"
    
    # Copy project files
    rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
          . $USERNAME@$NODE:$PROJECT_DIR/
    
    echo "✅ Deployment to $NODE completed"
done

echo "🎯 Starting cluster nodes..."

# Start each node
for i in "${!NODES[@]}"; do
    NODE=${NODES[$i]}
    NODE_ID=$((i+1))
    API_PORT=$((5000+NODE_ID))
    RAFT_PORT=$((4320+NODE_ID))
    
    echo "🔥 Starting node $NODE_ID on $NODE"
    
    # Create start command for this node
    if [ $i -eq 0 ]; then
        # First node (leader)
        ssh $USERNAME@$NODE "cd $PROJECT_DIR && nohup python3 -m src.main --node-id node$NODE_ID --api-port $API_PORT --raft-port $RAFT_PORT --leader > node$NODE_ID.log 2>&1 &"
    else
        # Follower nodes
        LEADER_IP=${NODES[0]}
        ssh $USERNAME@$NODE "cd $PROJECT_DIR && nohup python3 -m src.main --node-id node$NODE_ID --api-port $API_PORT --raft-port $RAFT_PORT --leader-addr $LEADER_IP:4321 > node$NODE_ID.log 2>&1 &"
    fi
    
    sleep 2
done

echo "✅ Cluster deployment completed!"
echo ""
echo "🔍 Verify cluster status:"
for NODE in "${NODES[@]}"; do
    echo "  Node $NODE: http://$NODE:$((5000 + ${#NODES[@]}))/graph"
done
```

Make the script executable and run it:

```bash
chmod +x deploy_to_rpi.sh
./deploy_to_rpi.sh
```

### 5. Test the Raspberry Pi Cluster

Create a test script for the cluster:

```bash
#!/bin/bash
# test_rpi_cluster.sh

NODES=("192.168.1.101:5001" "192.168.1.102:5002" "192.168.1.103:5003")

echo "🧪 Testing RAC-NAS Raspberry Pi Cluster"
echo "======================================="

# Test 1: Add a subject
echo "📝 Test 1: Adding subject 'rpi_alice'"
curl -X POST http://${NODES[0]}/subject \
     -H 'Content-Type: application/json' \
     -d '{"id": "rpi_alice"}' \
     -w "\nStatus: %{http_code}\n"

sleep 1

# Test 2: Add an object  
echo ""
echo "📝 Test 2: Adding object 'cluster_file.txt'"
curl -X POST http://${NODES[1]}/object \
     -H 'Content-Type: application/json' \
     -d '{"id": "cluster_file.txt"}' \
     -w "\nStatus: %{http_code}\n"

sleep 1

# Test 3: Assign rights
echo ""
echo "📝 Test 3: Assigning write rights"
curl -X POST http://${NODES[2]}/assign \
     -H 'Content-Type: application/json' \
     -d '{"src": "rpi_alice", "dst": "cluster_file.txt", "right": "write"}' \
     -w "\nStatus: %{http_code}\n"

sleep 2

# Test 4: Check graph consistency across nodes
echo ""
echo "📊 Test 4: Verifying graph consistency across nodes"
for i in "${!NODES[@]}"; do
    echo ""
    echo "--- Node $((i+1)): ${NODES[$i]} ---"
    curl -s http://${NODES[$i]}/graph | python3 -m json.tool
done

# Test 5: File operations
echo ""
echo "📁 Test 5: Testing file operations"
curl -X POST http://${NODES[0]}/write \
     -H 'Content-Type: application/json' \
     -d '{"subject": "rpi_alice", "object": "cluster_file.txt", "content": "Hello from Raspberry Pi cluster!"}' \
     -w "\nStatus: %{http_code}\n"

echo ""
echo "✅ Cluster testing completed!"
```

Run the cluster test:

```bash
chmod +x test_rpi_cluster.sh
./test_rpi_cluster.sh
```

### 6. Run Unit Tests on Raspberry Pi

You can also run the full test suite on the Raspberry Pi cluster:

```bash
# Copy and run tests on the leader node
scp ./run_tests.sh pi@192.168.1.101:/home/pi/Resilient-Access-Control/
ssh pi@192.168.1.101 "cd /home/pi/Resilient-Access-Control && chmod +x run_tests.sh && ./run_tests.sh"
```

### 7. Monitor and Manage the Cluster

Create management commands:

```bash
#!/bin/bash
# manage_rpi_cluster.sh

NODES=("192.168.1.101" "192.168.1.102" "192.168.1.103")
USERNAME="pi"
PROJECT_DIR="/home/pi/Resilient-Access-Control"

case "$1" in
    "status")
        echo "🔍 Checking cluster status..."
        for NODE in "${NODES[@]}"; do
            echo "Node $NODE:"
            ssh $USERNAME@$NODE "pgrep -f 'python3.*src.main' && echo '  ✅ Running' || echo '  ❌ Stopped'"
        done
        ;;
    
    "stop")
        echo "🛑 Stopping cluster..."
        for NODE in "${NODES[@]}"; do
            ssh $USERNAME@$NODE "pkill -f 'python3.*src.main'"
            echo "  ✅ Stopped $NODE"
        done
        ;;
    
    "logs")
        echo "📋 Fetching logs..."
        for i in "${!NODES[@]}"; do
            NODE=${NODES[$i]}
            NODE_ID=$((i+1))
            echo "--- Node $NODE_ID logs ---"
            ssh $USERNAME@$NODE "tail -20 $PROJECT_DIR/node$NODE_ID.log"
        done
        ;;
    
    "restart")
        echo "🔄 Restarting cluster..."
        $0 stop
        sleep 3
        ./deploy_to_rpi.sh
        ;;
    
    *)
        echo "Usage: $0 {status|stop|logs|restart}"
        ;;
esac
```

Usage examples:

```bash
chmod +x manage_rpi_cluster.sh

# Check cluster status
./manage_rpi_cluster.sh status

# View logs
./manage_rpi_cluster.sh logs

# Stop cluster
./manage_rpi_cluster.sh stop

# Restart cluster
./manage_rpi_cluster.sh restart
```

### Raspberry Pi Specific Features

- **🔌 Automatic deployment** across multiple physical devices via SSH
- **📡 Network-based communication** between Raspberry Pi nodes
- **🔍 Remote monitoring** and status checking
- **📦 File synchronization** using rsync for code deployment
- **⚙️ Process management** for starting/stopping nodes remotely
- **🧪 Distributed testing** to verify cluster functionality
- **📊 Real-time graph replication** across physical hardware
- **🛡️ Fault tolerance** testing with actual node disconnections

### Performance Considerations for Raspberry Pi

- **Memory**: Each node requires ~50-100MB RAM for the Python process
- **Network**: Raft consensus requires stable network connectivity
- **Storage**: File operations will use local storage on each Pi
- **CPU**: Graph operations are lightweight but consensus can be CPU-intensive
- **Latency**: Network latency between Pis affects consensus performance

Your Raspberry Pi cluster will provide a realistic distributed environment for testing the RAC-NAS system's fault tolerance and consistency guarantees!

---

## What This Repository Does

This repository implements a **distributed, fault-tolerant access control system** using the **Schematic Protection Model (SPM)**. The system is designed to run on a cluster of nodes, with each node maintaining a local instance of the access control graph. The nodes use **PySyncObj**, a Raft-based consensus library, to replicate changes to the graph across the cluster.

### Key Features

- **Graph-Based Access Control**:  
  Subjects (users) and objects (resources) are represented as nodes in a directed graph. Edges between nodes represent access rights (e.g., `read`, `write`, `grant`, `take`).

- **Distributed Consensus with PySyncObj**:  
  All changes to the graph (e.g., adding subjects, assigning rights) are replicated across the cluster using the Raft consensus algorithm, ensuring consistency even in the presence of node failures.

- **REST API**:  
  A Flask-based API provides endpoints for managing subjects, objects, and access rights, as well as querying the current state of the graph.

- **Fault Tolerance**:  
  The system is resilient to node crashes and network partitions, ensuring that access control policies remain consistent across the cluster.

### How It Works

1. **SPM Graph**:  
   The core of the system is the `SPMGraph` class, which models the access control graph. It supports operations like adding subjects/objects, assigning rights, and serializing/deserializing the graph.

2. **Replication Layer**:  
   The `GraphCluster` class wraps the `SPMGraph` and uses PySyncObj to replicate graph mutations across all nodes in the cluster. Mutating methods (e.g., `add_subject`, `assign_right`) are marked with the `@replicated` decorator to ensure they are logged and executed on all nodes.

3. **REST API**:  
   The API routes in `src/api/routes.py` interact with the `GraphCluster` to handle requests. For example, when a client sends a request to add a subject, the API calls the `add_subject` method on the cluster, which replicates the change across all nodes.

4. **Dockerized Deployment**:  
   The system is containerized using Docker, making it easy to deploy on any platform. Each node runs as a separate container, and the nodes communicate over a custom Docker network.


## Example Use Case

Imagine a distributed file storage system where users need fine-grained access control over shared files. This repository provides the backend logic to enforce such policies. example:

- Alice can grant Bob `read` access to a file she owns.
- Bob can take `write` access from Alice if he has the `take` right.
- The system ensures that these changes are replicated across all nodes, so every node enforces the same policies.

## Contributing

Contributions are welcome! If you find a bug or have an idea for a new feature, feel free to open an issue or submit a pull request.

```bash
git checkout -b feature/your-feature-name
git commit -m "Add your feature"
git push origin feature/your-feature-name
```
