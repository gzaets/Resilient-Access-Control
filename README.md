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

## Contributors

- **Zeerak Babar** – zebabar@ucdavis.edu
- **Anant Vishwakarma** – abvishwakarma@ucdavis.edu
- **Georgy Zaets** – gzaets@ucdavis.edu
