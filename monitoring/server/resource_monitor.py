"""
Resource Monitor - CPU, Memory, and Disk Monitoring
Monitors system resources for anomaly detection
"""

import psutil
import logging
from datetime import datetime
from typing import Dict, Any, List
import os

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor system resources (CPU, memory, disk)"""
    
    def __init__(self):
        """Initialize resource monitor"""
        self.cpu_threshold = 90.0  # CPU usage threshold (%)
        self.memory_threshold = 95.0  # Memory usage threshold (%)
        self.disk_threshold = 90.0  # Disk usage threshold (%)
    
    def get_cpu_usage(self) -> Dict[str, Any]:
        """
        Get current CPU usage
        
        Returns:
            Dictionary with CPU usage information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'cpu_count': cpu_count,
                'cpu_per_core': [round(c, 2) for c in cpu_per_core],
                'timestamp': datetime.now().isoformat(),
                'threshold_exceeded': cpu_percent > self.cpu_threshold
            }
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return {
                'cpu_percent': 0,
                'error': str(e)
            }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get current memory usage
        
        Returns:
            Dictionary with memory usage information
        """
        try:
            memory = psutil.virtual_memory()
            
            return {
                'memory_percent': round(memory.percent, 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_free_gb': round(memory.free / (1024**3), 2),
                'timestamp': datetime.now().isoformat(),
                'threshold_exceeded': memory.percent > self.memory_threshold
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {
                'memory_percent': 0,
                'error': str(e)
            }
    
    def get_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """
        Get disk usage for a specific path
        
        Args:
            path: Path to check disk usage for
            
        Returns:
            Dictionary with disk usage information
        """
        try:
            disk = psutil.disk_usage(path)
            
            return {
                'disk_percent': round(disk.percent, 2),
                'disk_total_gb': round(disk.total / (1024**3), 2),
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'path': path,
                'timestamp': datetime.now().isoformat(),
                'threshold_exceeded': disk.percent > self.disk_threshold
            }
        except Exception as e:
            logger.error(f"Error getting disk usage for {path}: {e}")
            return {
                'disk_percent': 0,
                'error': str(e)
            }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network statistics
        
        Returns:
            Dictionary with network statistics
        """
        try:
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'active_connections': connections,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return {
                'error': str(e)
            }
    
    def get_all_resources(self) -> Dict[str, Any]:
        """
        Get all resource metrics
        
        Returns:
            Dictionary with all resource information
        """
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_stats(),
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_resource_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect resource anomalies (threshold exceeded)
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Check CPU
        cpu = self.get_cpu_usage()
        if cpu.get('threshold_exceeded', False):
            anomalies.append({
                'type': 'cpu_exhaustion',
                'severity': 'high',
                'message': f"CPU usage is {cpu.get('cpu_percent')}% (threshold: {self.cpu_threshold}%)",
                'value': cpu.get('cpu_percent'),
                'threshold': self.cpu_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check Memory
        memory = self.get_memory_usage()
        if memory.get('threshold_exceeded', False):
            anomalies.append({
                'type': 'memory_exhaustion',
                'severity': 'high',
                'message': f"Memory usage is {memory.get('memory_percent')}% (threshold: {self.memory_threshold}%)",
                'value': memory.get('memory_percent'),
                'threshold': self.memory_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check Disk
        disk = self.get_disk_usage()
        if disk.get('threshold_exceeded', False):
            anomalies.append({
                'type': 'disk_full',
                'severity': 'high',
                'message': f"Disk usage is {disk.get('disk_percent')}% (threshold: {self.disk_threshold}%)",
                'value': disk.get('disk_percent'),
                'threshold': self.disk_threshold,
                'timestamp': datetime.now().isoformat()
            })
        
        return anomalies

