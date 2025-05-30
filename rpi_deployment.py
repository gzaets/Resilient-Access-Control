#!/usr/bin/env python3
"""
Raspberry Pi Deployment Manager for Resilient Access Control NAS
================================================================

This module provides utilities for deploying and managing the RAC-NAS system
across physical Raspberry Pi devices. It handles configuration, deployment,
health monitoring, and cluster management.

Usage:
    python3 rpi_deployment.py --action deploy --config rpi_cluster.json
    python3 rpi_deployment.py --action status --config rpi_cluster.json
    python3 rpi_deployment.py --action start-node --node rpi-node-1
"""

import argparse
import json
import subprocess
import sys
import time
import os
from typing import Dict, List, Optional
import requests
import paramiko
from pathlib import Path

class RaspberryPiCluster:
    """Manages deployment and operations of RAC-NAS on Raspberry Pi cluster."""
    
    def __init__(self, config_file: str):
        """Initialize cluster manager with configuration file."""
        self.config_file = config_file
        self.config = self._load_config()
        self.nodes = self.config.get("nodes", {})
        self.ssh_key = self.config.get("ssh_key_path", "~/.ssh/id_rsa")
        self.username = self.config.get("username", "pi")
        self.project_path = self.config.get("remote_project_path", "/home/pi/Resilient-Access-Control")
        
    def _load_config(self) -> Dict:
        """Load cluster configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_file} not found!")
            self._create_sample_config()
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {self.config_file}: {e}")
            sys.exit(1)
    
    def _create_sample_config(self):
        """Create a sample configuration file."""
        sample_config = {
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
        
        sample_file = "rpi_cluster_sample.json"
        with open(sample_file, 'w') as f:
            json.dump(sample_config, f, indent=2)
        print(f"📝 Created sample configuration: {sample_file}")
        print("   Please copy and modify it to match your Raspberry Pi setup.")
    
    def _ssh_connect(self, ip: str) -> paramiko.SSHClient:
        """Establish SSH connection to a Raspberry Pi."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(
                hostname=ip,
                username=self.username,
                key_filename=os.path.expanduser(self.ssh_key),
                timeout=10
            )
            return ssh
        except Exception as e:
            print(f"❌ Failed to connect to {ip}: {e}")
            return None
    
    def _run_remote_command(self, ip: str, command: str) -> tuple:
        """Execute a command on a remote Raspberry Pi."""
        ssh = self._ssh_connect(ip)
        if not ssh:
            return False, "", "SSH connection failed"
        
        try:
            stdin, stdout, stderr = ssh.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_str = stdout.read().decode('utf-8')
            stderr_str = stderr.read().decode('utf-8')
            ssh.close()
            return exit_code == 0, stdout_str, stderr_str
        except Exception as e:
            ssh.close()
            return False, "", str(e)
    
    def deploy_to_cluster(self):
        """Deploy the RAC-NAS system to all Raspberry Pis in the cluster."""
        print("🚀 Starting deployment to Raspberry Pi cluster...")
        
        # Step 1: Copy project files to each node
        for node_name, node_config in self.nodes.items():
            ip = node_config["ip"]
            print(f"📦 Deploying to {node_name} ({ip})...")
            
            if not self._copy_project_files(ip):
                print(f"❌ Failed to copy files to {node_name}")
                continue
            
            if not self._install_dependencies(ip):
                print(f"❌ Failed to install dependencies on {node_name}")
                continue
                
            print(f"✅ Successfully deployed to {node_name}")
        
        print("📋 Deployment completed! Use 'start-cluster' to begin the cluster.")
    
    def _copy_project_files(self, ip: str) -> bool:
        """Copy project files to a Raspberry Pi using rsync."""
        current_dir = os.getcwd()
        
        # Use rsync to copy files (more efficient than scp for directories)
        rsync_cmd = [
            "rsync", "-avz", "--delete",
            "--exclude=__pycache__",
            "--exclude=.git",
            "--exclude=*.pyc",
            "--exclude=.venv",
            f"{current_dir}/",
            f"{self.username}@{ip}:{self.project_path}/"
        ]
        
        try:
            result = subprocess.run(rsync_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✓ Files copied to {ip}")
                return True
            else:
                print(f"  ❌ rsync failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"  ❌ Error copying files: {e}")
            return False
    
    def _install_dependencies(self, ip: str) -> bool:
        """Install Python dependencies on a Raspberry Pi."""
        commands = [
            "sudo apt update",
            "sudo apt install -y python3-pip",
            f"cd {self.project_path} && pip3 install -r requirements-main.txt"
        ]
        
        for cmd in commands:
            success, stdout, stderr = self._run_remote_command(ip, cmd)
            if not success:
                print(f"  ❌ Command failed: {cmd}")
                print(f"     Error: {stderr}")
                return False
        
        print(f"  ✓ Dependencies installed on {ip}")
        return True
    
    def start_cluster(self):
        """Start the RAC-NAS cluster on all Raspberry Pis."""
        print("🔄 Starting RAC-NAS cluster...")
        
        # Generate partner addresses for each node
        all_addresses = [f"{node['ip']}:{node['port']}" for node in self.nodes.values()]
        
        for node_name, node_config in self.nodes.items():
            ip = node_config["ip"]
            port = node_config["port"]
            api_port = node_config["api_port"]
            
            # Create partner list (all nodes except current)
            self_addr = f"{ip}:{port}"
            partner_addrs = [addr for addr in all_addresses if addr != self_addr]
            partners_str = ",".join(partner_addrs)
            
            # Start the node
            print(f"🚀 Starting {node_name} ({ip})...")
            if self._start_node(ip, self_addr, partners_str, api_port):
                print(f"  ✓ {node_name} started successfully")
            else:
                print(f"  ❌ Failed to start {node_name}")
        
        # Wait for cluster to initialize
        print("⏳ Waiting for cluster to initialize...")
        time.sleep(10)
        
        # Verify cluster status
        self.check_cluster_status()
    
    def _start_node(self, ip: str, self_addr: str, partners: str, api_port: int) -> bool:
        """Start a single RAC-NAS node on a Raspberry Pi."""
        
        # Stop any existing instance first
        stop_cmd = f"pkill -f 'python3.*main.py' || true"
        self._run_remote_command(ip, stop_cmd)
        
        # Start the node in background
        start_cmd = (
            f"cd {self.project_path} && "
            f"SELF_ADDR='{self_addr}' PARTNERS='{partners}' "
            f"nohup python3 -m src.app.main > rac_node.log 2>&1 & echo $!"
        )
        
        success, stdout, stderr = self._run_remote_command(ip, start_cmd)
        if success and stdout.strip().isdigit():
            pid = stdout.strip()
            print(f"  ✓ Node started with PID {pid}")
            return True
        else:
            print(f"  ❌ Failed to start node: {stderr}")
            return False
    
    def stop_cluster(self):
        """Stop all RAC-NAS nodes in the cluster."""
        print("🛑 Stopping RAC-NAS cluster...")
        
        for node_name, node_config in self.nodes.items():
            ip = node_config["ip"]
            print(f"🛑 Stopping {node_name} ({ip})...")
            
            stop_cmd = "pkill -f 'python3.*main.py'"
            success, stdout, stderr = self._run_remote_command(ip, stop_cmd)
            
            if success or "no process found" in stderr.lower():
                print(f"  ✓ {node_name} stopped")
            else:
                print(f"  ❌ Error stopping {node_name}: {stderr}")
    
    def check_cluster_status(self):
        """Check the status of all nodes in the cluster."""
        print("📊 Checking cluster status...")
        
        for node_name, node_config in self.nodes.items():
            ip = node_config["ip"]
            api_port = node_config.get("api_port", 5000)
            
            try:
                response = requests.get(f"http://{ip}:{api_port}/graph", timeout=5)
                if response.status_code == 200:
                    graph_data = response.json()
                    node_count = len(graph_data.get("nodes", []))
                    edge_count = len(graph_data.get("edges", []))
                    print(f"  ✅ {node_name} ({ip}): Online - {node_count} nodes, {edge_count} edges")
                else:
                    print(f"  ❌ {node_name} ({ip}): HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {node_name} ({ip}): Offline - {e}")
    
    def test_cluster(self):
        """Run basic functionality tests on the cluster."""
        print("🧪 Testing cluster functionality...")
        
        # Use the first node for testing
        first_node = list(self.nodes.values())[0]
        api_url = f"http://{first_node['ip']}:{first_node.get('api_port', 5000)}"
        
        try:
            # Test 1: Add a subject
            print("  📤 Adding test subject...")
            response = requests.post(f"{api_url}/subject", 
                                   json={"id": "test_user"}, timeout=10)
            if response.status_code == 201:
                print("    ✓ Subject added successfully")
            else:
                print(f"    ❌ Failed to add subject: {response.status_code}")
                return
            
            # Test 2: Add an object
            print("  📁 Adding test object...")
            response = requests.post(f"{api_url}/object", 
                                   json={"id": "test_file.txt"}, timeout=10)
            if response.status_code == 201:
                print("    ✓ Object added successfully")
            else:
                print(f"    ❌ Failed to add object: {response.status_code}")
                return
            
            # Test 3: Check replication across nodes
            print("  🔄 Checking replication across nodes...")
            time.sleep(2)  # Allow time for replication
            
            for node_name, node_config in self.nodes.items():
                ip = node_config["ip"]
                api_port = node_config.get("api_port", 5000)
                
                try:
                    response = requests.get(f"http://{ip}:{api_port}/graph", timeout=5)
                    if response.status_code == 200:
                        graph_data = response.json()
                        nodes = [n["id"] for n in graph_data.get("nodes", [])]
                        if "test_user" in nodes and "test_file.txt" in nodes:
                            print(f"    ✅ {node_name}: Replication successful")
                        else:
                            print(f"    ❌ {node_name}: Missing test nodes")
                    else:
                        print(f"    ❌ {node_name}: HTTP {response.status_code}")
                except requests.exceptions.RequestException:
                    print(f"    ❌ {node_name}: Connection failed")
            
            print("🎉 Cluster test completed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")


def main():
    """Main entry point for the Raspberry Pi deployment manager."""
    parser = argparse.ArgumentParser(description="Raspberry Pi Cluster Manager for RAC-NAS")
    parser.add_argument("--action", required=True, 
                       choices=["deploy", "start-cluster", "stop-cluster", "status", "test"],
                       help="Action to perform")
    parser.add_argument("--config", default="rpi_cluster.json",
                       help="Cluster configuration file (default: rpi_cluster.json)")
    
    args = parser.parse_args()
    
    cluster = RaspberryPiCluster(args.config)
    
    if args.action == "deploy":
        cluster.deploy_to_cluster()
    elif args.action == "start-cluster":
        cluster.start_cluster()
    elif args.action == "stop-cluster":
        cluster.stop_cluster()
    elif args.action == "status":
        cluster.check_cluster_status()
    elif args.action == "test":
        cluster.test_cluster()


if __name__ == "__main__":
    main()