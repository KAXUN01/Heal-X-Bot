"""
Container Monitor - Docker Container Health Monitoring
Monitors Docker containers for the cloud simulation environment
"""

import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import docker
from docker.errors import DockerException, APIError

logger = logging.getLogger(__name__)

class ContainerMonitor:
    """Monitor Docker container health and status"""
    
    def __init__(self, compose_file: str = None):
        """
        Initialize container monitor
        
        Args:
            compose_file: Path to docker-compose file (optional)
        """
        self.compose_file = compose_file
        self.docker_client = None
        # Removed hardcoded cloud-sim containers - will discover containers dynamically
        self.monitored_containers = []
        
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.warning(f"Docker client not available: {e}")
            self.docker_client = None
    
    def get_container_status(self, container_name: str) -> Dict[str, Any]:
        """
        Get status of a specific container
        
        Args:
            container_name: Name of the container
            
        Returns:
            Dictionary with container status information
        """
        if not self.docker_client:
            return {
                'name': container_name,
                'status': 'unknown',
                'error': 'Docker client not available'
            }
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Get container stats
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
            
            # Calculate memory usage
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 1)
            memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            
            return {
                'name': container_name,
                'status': container.status,
                'state': container.attrs['State']['Status'],
                'health': container.attrs['State'].get('Health', {}).get('Status', 'unknown'),
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
                'started_at': container.attrs['State'].get('StartedAt', ''),
                'restart_count': container.attrs.get('RestartCount', 0),
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
                'is_running': container.status == 'running',
                'is_healthy': container.attrs['State'].get('Health', {}).get('Status', '') == 'healthy'
            }
        except docker.errors.NotFound:
            return {
                'name': container_name,
                'status': 'not_found',
                'state': 'not_found',
                'is_running': False,
                'is_healthy': False,
                'error': 'Container not found'
            }
        except Exception as e:
            logger.error(f"Error getting container status for {container_name}: {e}")
            return {
                'name': container_name,
                'status': 'error',
                'state': 'error',
                'is_running': False,
                'is_healthy': False,
                'error': str(e)
            }
    
    def get_all_containers_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all containers (excluding cloud-sim containers)
        
        Returns:
            List of container status dictionaries
        """
        containers_status = []
        
        if not self.docker_client:
            return containers_status
        
        try:
            # Get all containers (running and stopped)
            all_containers = self.docker_client.containers.list(all=True)
            
            for container in all_containers:
                container_name = container.name
                
                # Filter out cloud-sim containers
                if container_name.startswith('cloud-sim'):
                    continue
                
                status = self.get_container_status(container_name)
                # Add service type indicator
                status['type'] = 'docker'
                containers_status.append(status)
        except Exception as e:
            logger.error(f"Error getting all containers status: {e}")
        
        return containers_status
    
    def check_container_health(self, container_name: str) -> Dict[str, Any]:
        """
        Check if a container is healthy
        
        Returns:
            Health check result
        """
        status = self.get_container_status(container_name)
        
        health_result = {
            'container': container_name,
            'timestamp': datetime.now().isoformat(),
            'healthy': False,
            'issues': []
        }
        
        if status.get('status') == 'not_found':
            health_result['issues'].append('Container not found')
            return health_result
        
        if not status.get('is_running', False):
            health_result['issues'].append('Container is not running')
            return health_result
        
        # Check health status
        if status.get('health') == 'unhealthy':
            health_result['issues'].append('Container health check failed')
        
        # Check resource usage
        if status.get('cpu_percent', 0) > 90:
            health_result['issues'].append(f"High CPU usage: {status.get('cpu_percent')}%")
        
        if status.get('memory_percent', 0) > 95:
            health_result['issues'].append(f"High memory usage: {status.get('memory_percent')}%")
        
        # If no issues, container is healthy
        if not health_result['issues']:
            health_result['healthy'] = True
        
        return health_result
    
    def detect_crashed_containers(self) -> List[Dict[str, Any]]:
        """
        Detect containers that have crashed or stopped
        
        Returns:
            List of crashed container information
        """
        crashed = []
        
        if not self.docker_client:
            return crashed
        
        try:
            # Get all containers (running and stopped)
            all_containers = self.docker_client.containers.list(all=True)
            
            for container in all_containers:
                container_name = container.name
                
                # Filter out cloud-sim containers
                if container_name.startswith('cloud-sim'):
                    continue
                
                status = self.get_container_status(container_name)
                
                # Check if container is not running when it should be
                if status.get('status') in ['exited', 'stopped', 'dead']:
                    crashed.append({
                        'container': container_name,
                        'status': status.get('status', 'unknown'),
                        'state': status.get('state', 'unknown'),
                        'restart_count': status.get('restart_count', 0),
                        'timestamp': datetime.now().isoformat(),
                        'error': status.get('error', 'Container stopped or crashed')
                    })
        except Exception as e:
            logger.error(f"Error detecting crashed containers: {e}")
        
        return crashed
    
    def get_container_logs(self, container_name: str, tail: int = 50) -> List[str]:
        """
        Get recent logs from a container
        
        Args:
            container_name: Name of the container
            tail: Number of lines to retrieve
            
        Returns:
            List of log lines
        """
        if not self.docker_client:
            return []
        
        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs.split('\n') if logs else []
        except Exception as e:
            logger.error(f"Error getting logs for {container_name}: {e}")
            return []

