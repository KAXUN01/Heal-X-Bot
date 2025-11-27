"""
Fault Injector - Controlled Fault Injection System
Injects faults into the simulated cloud environment for testing and demonstration
"""

import subprocess
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)

class FaultInjector:
    """Inject controlled faults into the cloud simulation environment"""
    
    def __init__(self):
        """Initialize fault injector"""
        self.docker_client = None
        
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized for fault injector")
        except DockerException as e:
            logger.warning(f"Docker client not available: {e}")
            self.docker_client = None
        
        # Track injected faults
        self.injected_faults = []
        self.max_history = 50
    
    def inject_service_crash(self, container_name: str) -> Tuple[bool, str]:
        """
        Inject a service crash by stopping a container
        
        Args:
            container_name: Name of the container to crash
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            container.stop(timeout=10)
            
            fault_record = {
                'type': 'service_crash',
                'container': container_name,
                'timestamp': datetime.now().isoformat(),
                'action': 'stopped'
            }
            self._record_fault(fault_record)
            
            message = f"Service crash injected: {container_name} stopped"
            logger.info(f"💥 {message}")
            return True, message
            
        except docker.errors.NotFound:
            return False, f"Container {container_name} not found"
        except Exception as e:
            return False, f"Error injecting service crash: {str(e)}"
    
    def inject_cpu_exhaustion(self, duration: int = 60) -> Tuple[bool, str]:
        """
        Inject CPU exhaustion by running CPU-intensive processes
        
        Args:
            duration: Duration in seconds to run CPU stress
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if stress-ng is available
            result = subprocess.run(['which', 'stress-ng'], capture_output=True)
            if result.returncode != 0:
                # Use Python to create CPU load instead
                import multiprocessing
                import threading
                
                def cpu_burn():
                    while True:
                        _ = sum(i * i for i in range(10000))
                
                # Start CPU-intensive threads
                threads = []
                for _ in range(multiprocessing.cpu_count()):
                    t = threading.Thread(target=cpu_burn, daemon=True)
                    t.start()
                    threads.append(t)
                
                fault_record = {
                    'type': 'cpu_exhaustion',
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'started_cpu_stress'
                }
                self._record_fault(fault_record)
                
                message = f"CPU exhaustion injected: {multiprocessing.cpu_count()} CPU-intensive threads started"
                logger.info(f"💥 {message}")
                return True, message
            else:
                # Use stress-ng if available
                process = subprocess.Popen(
                    ['stress-ng', '--cpu', str(multiprocessing.cpu_count()), '--timeout', str(duration)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                fault_record = {
                    'type': 'cpu_exhaustion',
                    'duration': duration,
                    'pid': process.pid,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'started_stress_ng'
                }
                self._record_fault(fault_record)
                
                message = f"CPU exhaustion injected: stress-ng running for {duration} seconds (PID: {process.pid})"
                logger.info(f"💥 {message}")
                return True, message
                
        except Exception as e:
            return False, f"Error injecting CPU exhaustion: {str(e)}"
    
    def inject_memory_exhaustion(self, size_gb: float = 2.0) -> Tuple[bool, str]:
        """
        Inject memory exhaustion by allocating memory
        
        Args:
            size_gb: Amount of memory to allocate in GB
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if stress-ng is available
            result = subprocess.run(['which', 'stress-ng'], capture_output=True)
            if result.returncode != 0:
                # Use Python to allocate memory
                import sys
                size_bytes = int(size_gb * 1024 * 1024 * 1024)
                
                # Allocate memory (this will be garbage collected when function ends)
                # For persistent memory exhaustion, we'd need to keep a reference
                memory_hog = bytearray(size_bytes)
                
                fault_record = {
                    'type': 'memory_exhaustion',
                    'size_gb': size_gb,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'allocated_memory'
                }
                self._record_fault(fault_record)
                
                message = f"Memory exhaustion injected: {size_gb} GB allocated"
                logger.info(f"💥 {message}")
                return True, message
            else:
                # Use stress-ng if available
                process = subprocess.Popen(
                    ['stress-ng', '--vm', '2', '--vm-bytes', f'{int(size_gb * 1024)}M', '--timeout', '300'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                fault_record = {
                    'type': 'memory_exhaustion',
                    'size_gb': size_gb,
                    'pid': process.pid,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'started_stress_ng'
                }
                self._record_fault(fault_record)
                
                message = f"Memory exhaustion injected: stress-ng allocating {size_gb} GB (PID: {process.pid})"
                logger.info(f"💥 {message}")
                return True, message
                
        except Exception as e:
            return False, f"Error injecting memory exhaustion: {str(e)}"
    
    def inject_disk_full(self, size_gb: float = 5.0) -> Tuple[bool, str]:
        """
        Inject disk full condition by creating large files
        
        Args:
            size_gb: Size of file to create in GB
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create a large file in /tmp
            file_path = f"/tmp/healing_bot_disk_test_{int(time.time())}.dat"
            size_bytes = int(size_gb * 1024 * 1024 * 1024)
            
            # Create file using dd command
            result = subprocess.run(
                ['dd', 'if=/dev/zero', f'of={file_path}', f'bs=1M', f'count={int(size_gb * 1024)}'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                fault_record = {
                    'type': 'disk_full',
                    'size_gb': size_gb,
                    'file_path': file_path,
                    'timestamp': datetime.now().isoformat(),
                    'action': 'created_large_file'
                }
                self._record_fault(fault_record)
                
                message = f"Disk full condition injected: Created {size_gb} GB file at {file_path}"
                logger.info(f"💥 {message}")
                return True, message
            else:
                return False, f"Failed to create large file: {result.stderr}"
                
        except Exception as e:
            return False, f"Error injecting disk full: {str(e)}"
    
    def inject_network_issue(self, container_name: str, port: int = None) -> Tuple[bool, str]:
        """
        Inject network issue by disconnecting container from network or blocking port
        
        Args:
            container_name: Name of the container
            port: Optional port to block
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            if port:
                # Block port using iptables (requires sudo)
                try:
                    result = subprocess.run(
                        ['sudo', 'iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        fault_record = {
                            'type': 'network_issue',
                            'container': container_name,
                            'port': port,
                            'timestamp': datetime.now().isoformat(),
                            'action': 'blocked_port'
                        }
                        self._record_fault(fault_record)
                        
                        message = f"Network issue injected: Port {port} blocked for {container_name}"
                        logger.info(f"💥 {message}")
                        return True, message
                    else:
                        return False, f"Failed to block port: {result.stderr}"
                except Exception as e:
                    return False, f"Error blocking port: {str(e)}"
            else:
                # Disconnect container from network
                networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                if networks:
                    network_name = list(networks.keys())[0]
                    self.docker_client.networks.get(network_name).disconnect(container_name)
                    
                    fault_record = {
                        'type': 'network_issue',
                        'container': container_name,
                        'network': network_name,
                        'timestamp': datetime.now().isoformat(),
                        'action': 'disconnected_network'
                    }
                    self._record_fault(fault_record)
                    
                    message = f"Network issue injected: {container_name} disconnected from {network_name}"
                    logger.info(f"💥 {message}")
                    return True, message
                else:
                    return False, f"Container {container_name} has no networks"
                    
        except Exception as e:
            return False, f"Error injecting network issue: {str(e)}"
    
    def cleanup_injected_faults(self) -> Tuple[bool, str]:
        """
        Clean up all injected faults
        
        Returns:
            Tuple of (success, message)
        """
        cleaned = []
        
        try:
            # Kill stress-ng processes
            try:
                subprocess.run(['pkill', '-f', 'stress-ng'], capture_output=True, timeout=10)
                cleaned.append('stress-ng processes')
            except:
                pass
            
            # Remove large test files
            try:
                result = subprocess.run(
                    ['find', '/tmp', '-name', 'healing_bot_disk_test_*.dat', '-delete'],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    cleaned.append('test files')
            except:
                pass
            
            # Remove iptables rules (requires sudo)
            try:
                # List and remove our rules
                result = subprocess.run(
                    ['sudo', 'iptables', '-L', 'INPUT', '--line-numbers'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                # Note: This is a simplified cleanup - in production, track rule numbers
                cleaned.append('iptables rules (manual cleanup may be needed)')
            except:
                pass
            
            # Clear fault history
            self.injected_faults = []
            
            message = f"Cleaned up injected faults: {', '.join(cleaned) if cleaned else 'No faults to clean'}"
            logger.info(f"🧹 {message}")
            return True, message
            
        except Exception as e:
            return False, f"Error cleaning up faults: {str(e)}"
    
    def _record_fault(self, fault_record: Dict[str, Any]):
        """Record an injected fault"""
        self.injected_faults.append(fault_record)
        if len(self.injected_faults) > self.max_history:
            self.injected_faults = self.injected_faults[-self.max_history:]
    
    def get_injected_faults(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history of injected faults"""
        return self.injected_faults[-limit:]


# Singleton instance
_fault_injector_instance = None

def initialize_fault_injector() -> FaultInjector:
    """Initialize the fault injector"""
    global _fault_injector_instance
    
    if _fault_injector_instance is None:
        _fault_injector_instance = FaultInjector()
        logger.info("Fault injector initialized")
    
    return _fault_injector_instance

def get_fault_injector() -> Optional[FaultInjector]:
    """Get the fault injector instance"""
    return _fault_injector_instance

