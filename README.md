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

The repository includes unit tests for the core functionality and API routes. To run the tests, use `pytest`:

```bash
pytest tests/
```

This will execute all tests in the `tests/` directory, ensuring that the SPM logic and API endpoints behave as expected.

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

Install Raspberry Pi deployment dependencies:

```bash
pip3 install -r requirements-rpi.txt
```

Create and edit the cluster configuration:

```bash
# This will create a sample configuration file
python3 rpi_deployment.py --action deploy --config rpi_cluster.json

# Edit the generated rpi_cluster_sample.json with your Raspberry Pi details
cp rpi_cluster_sample.json rpi_cluster.json
# Edit rpi_cluster.json with your actual IP addresses
```

Example `rpi_cluster.json`:
```json
{
  "username": "pi",
  "ssh_key_path": "~/.ssh/id_rsa",
  "remote_project_path": "/home/pi/Resilient-Access-Control",
  "nodes": {
    "rpi-node-1": {
      "ip": "192.168.1.101",
      "port": 4321,
      "api_port": 5001,
      "role": "leader"
    },
    "rpi-node-2": {
      "ip": "192.168.1.102",
      "port": 4321,
      "api_port": 5002,
      "role": "follower"
    },
    "rpi-node-3": {
      "ip": "192.168.1.103",
      "port": 4321,
      "api_port": 5003,
      "role": "follower"
    }
  }
}
```

### 4. Deploy to Raspberry Pi Cluster

Use the automated setup script:

```bash
chmod +x setup_rpi_cluster.sh
./setup_rpi_cluster.sh
```

Or manually deploy step by step:

```bash
# Deploy code and dependencies to all Raspberry Pis
python3 rpi_deployment.py --action deploy

# Start the cluster
python3 rpi_deployment.py --action start-cluster

# Check cluster status
python3 rpi_deployment.py --action status

# Run functionality tests
python3 rpi_deployment.py --action test
```

### 5. Test the Raspberry Pi Cluster

Run the cluster test script:

```bash
chmod +x test_rpi_cluster.sh
./test_rpi_cluster.sh
```

Or test manually using the API endpoints with your Raspberry Pi IPs:

```bash
# Add a subject
curl -X POST http://192.168.1.101:5001/subject \
     -H 'Content-Type: application/json' \
     -d '{"id": "pi_user"}'

# Check graph replication across nodes
curl http://192.168.1.101:5001/graph
curl http://192.168.1.102:5002/graph
curl http://192.168.1.103:5003/graph
```

### 6. Management Commands

```bash
# Check cluster status
python3 rpi_deployment.py --action status

# Stop the cluster
python3 rpi_deployment.py --action stop-cluster

# Restart the cluster
python3 rpi_deployment.py --action start-cluster

# Run tests
python3 rpi_deployment.py --action test
```

### Raspberry Pi Specific Features

- **Automatic deployment** across multiple physical devices
- **SSH-based management** for remote configuration
- **Health monitoring** and status checking
- **File synchronization** using rsync
- **Process management** for starting/stopping nodes
- **Network discovery** and cluster formation

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
