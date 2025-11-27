"""
Healing verification logic
"""
import subprocess
import socket
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def verify_healing(original_error: Dict[str, Any], 
                   system_log_collector=None) -> Dict[str, Any]:
    """
    Verify that the healing action resolved the error
    
    Args:
        original_error: Original error dictionary
        system_log_collector: System log collector instance
    
    Returns:
        verification result with success status
    """
    verification = {
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': 'log_check',
        'details': None
    }
    
    try:
        # Check if the same error still appears in recent logs
        if system_log_collector:
            recent_errors = system_log_collector.get_recent_logs(
                limit=5,
                level=original_error.get('level'),
                source=original_error.get('source')
            )
            
            # Check if the exact same error message appears
            error_msg = original_error.get('message', '')
            same_error_found = any(
                e.get('message') == error_msg 
                for e in recent_errors
            )
            
            if not same_error_found:
                verification['success'] = True
                verification['details'] = 'Error no longer appearing in logs'
            else:
                verification['success'] = False
                verification['details'] = 'Same error still appearing'
        
        # Additional verification: Check service status
        service = original_error.get('service', '')
        if service and verification['success']:
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    verification['service_status'] = 'active'
                else:
                    verification['service_status'] = 'inactive'
                    verification['success'] = False
            
            except:
                pass
    
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        verification['details'] = f'Verification error: {str(e)}'
    
    return verification


def verify_cloud_fault_healing(fault: Dict[str, Any], 
                               container_healer=None) -> Dict[str, Any]:
    """Verify that cloud fault healing was successful
    
    Args:
        fault: Fault information dictionary
        container_healer: Container healer instance
    
    Returns:
        Verification result dictionary
    """
    verification = {
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': 'container_check',
        'details': None
    }
    
    fault_type = fault.get('type', 'unknown')
    service = fault.get('service', '')
    
    try:
        if fault_type == 'service_crash':
            # Verify container is running
            if container_healer:
                container_name = service if service.startswith('cloud-sim-') else f'cloud-sim-{service}'
                health = container_healer.verify_container_health(container_name)
                
                if health.get('is_running', False):
                    verification['success'] = True
                    verification['details'] = f'Container {container_name} is running'
                else:
                    verification['details'] = f'Container {container_name} is not running'
        elif fault_type in ['cpu_exhaustion', 'memory_exhaustion', 'disk_full']:
            # Verify resource usage is below threshold
            try:
                from resource_monitor import ResourceMonitor
                monitor = ResourceMonitor()
                resources = monitor.get_all_resources()
                
                if fault_type == 'cpu_exhaustion':
                    cpu = resources.get('cpu', {}).get('cpu_percent', 0)
                    if cpu < 90:
                        verification['success'] = True
                        verification['details'] = f'CPU usage reduced to {cpu}%'
                elif fault_type == 'memory_exhaustion':
                    memory = resources.get('memory', {}).get('memory_percent', 0)
                    if memory < 95:
                        verification['success'] = True
                        verification['details'] = f'Memory usage reduced to {memory}%'
                elif fault_type == 'disk_full':
                    disk = resources.get('disk', {}).get('disk_percent', 0)
                    if disk < 90:
                        verification['success'] = True
                        verification['details'] = f'Disk usage reduced to {disk}%'
            except ImportError:
                verification['details'] = 'ResourceMonitor not available for verification'
        elif fault_type == 'network_issue':
            # Verify port is accessible
            port = fault.get('port', 0)
            if port > 0:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    verification['success'] = True
                    verification['details'] = f'Port {port} is now accessible'
                else:
                    verification['details'] = f'Port {port} is still not accessible'
    
    except Exception as e:
        logger.error(f"Error during cloud fault verification: {e}")
        verification['details'] = f'Verification error: {str(e)}'
    
    return verification

