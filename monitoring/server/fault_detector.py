"""
Fault Detector - Real-time Fault Detection Engine
Detects system faults, container crashes, resource exhaustion, and network issues
"""

import logging
import threading
import time
import socket
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from container_monitor import ContainerMonitor
from resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)

class FaultDetector:
    """Real-time fault detection engine"""
    
    def __init__(self, discord_notifier: Callable = None, event_emitter: Callable = None):
        """
        Initialize fault detector
        
        Args:
            discord_notifier: Function to send Discord notifications
            event_emitter: Function to emit events for dashboard (WebSocket)
        """
        self.container_monitor = ContainerMonitor()
        self.resource_monitor = ResourceMonitor()
        self.discord_notifier = discord_notifier
        self.event_emitter = event_emitter
        
        self.running = False
        self.monitoring_thread = None
        self.detection_interval = 30  # Check every 30 seconds
        
        # Track detected faults
        self.detected_faults = []
        self.max_fault_history = 100
        
        # Service ports to check
        self.service_ports = {
            'load-balancer': 8080,
            'web-server': 8081,
            'api-server': 8082,
            'database': 5432,
            'cache': 6379
        }
        
        logger.info("Fault Detector initialized")
    
    def start_monitoring(self, interval: int = 30):
        """
        Start continuous fault monitoring
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self.running:
            logger.warning("Fault detector already running")
            return
        
        self.detection_interval = interval
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Fault detector monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop fault monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Fault detector monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Detect all types of faults
                faults = self.detect_all_faults()
                
                # Process detected faults
                for fault in faults:
                    self._process_fault(fault)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(self.detection_interval)
    
    def detect_all_faults(self) -> List[Dict[str, Any]]:
        """
        Detect all types of faults
        
        Returns:
            List of detected faults
        """
        faults = []
        
        # 1. Detect container crashes
        container_faults = self.detect_container_crashes()
        faults.extend(container_faults)
        
        # 2. Detect resource exhaustion
        resource_faults = self.detect_resource_exhaustion()
        faults.extend(resource_faults)
        
        # 3. Detect network issues
        network_faults = self.detect_network_issues()
        faults.extend(network_faults)
        
        return faults
    
    def detect_container_crashes(self) -> List[Dict[str, Any]]:
        """
        Detect crashed or stopped containers
        
        Returns:
            List of container crash faults
        """
        faults = []
        crashed_containers = self.container_monitor.detect_crashed_containers()
        
        for container_info in crashed_containers:
            fault = {
                'type': 'service_crash',
                'severity': 'critical',
                'service': container_info['container'],
                'status': container_info.get('status', 'unknown'),
                'state': container_info.get('state', 'unknown'),
                'restart_count': container_info.get('restart_count', 0),
                'message': f"Service {container_info['container']} has crashed or stopped",
                'timestamp': datetime.now().isoformat(),
                'details': container_info
            }
            faults.append(fault)
        
        return faults
    
    def detect_resource_exhaustion(self) -> List[Dict[str, Any]]:
        """
        Detect resource exhaustion (CPU, memory, disk)
        
        Returns:
            List of resource exhaustion faults
        """
        faults = []
        anomalies = self.resource_monitor.detect_resource_anomalies()
        
        for anomaly in anomalies:
            fault = {
                'type': anomaly['type'],
                'severity': anomaly['severity'],
                'message': anomaly['message'],
                'value': anomaly['value'],
                'threshold': anomaly['threshold'],
                'timestamp': datetime.now().isoformat(),
                'details': anomaly
            }
            faults.append(fault)
        
        return faults
    
    def detect_network_issues(self) -> List[Dict[str, Any]]:
        """
        Detect network connectivity issues
        
        Returns:
            List of network fault information
        """
        faults = []
        
        # Check each service port
        for service_name, port in self.service_ports.items():
            if not self._check_port_connectivity('localhost', port):
                fault = {
                    'type': 'network_issue',
                    'severity': 'high',
                    'service': service_name,
                    'port': port,
                    'message': f"Service {service_name} is not reachable on port {port}",
                    'timestamp': datetime.now().isoformat()
                }
                faults.append(fault)
        
        return faults
    
    def _check_port_connectivity(self, host: str, port: int, timeout: int = 5) -> bool:
        """
        Check if a port is accessible
        
        Args:
            host: Host to check
            port: Port to check
            timeout: Connection timeout in seconds
            
        Returns:
            True if port is accessible, False otherwise
        """
        try:
            # For HTTP services, try HTTP request
            if port in [8080, 8081, 8082]:
                try:
                    response = requests.get(f"http://{host}:{port}/health", timeout=timeout)
                    return response.status_code == 200
                except:
                    pass
            
            # For database and cache, try socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.debug(f"Port connectivity check failed for {host}:{port}: {e}")
            return False
    
    def _process_fault(self, fault: Dict[str, Any]):
        """
        Process a detected fault
        
        Args:
            fault: Fault information dictionary
        """
        # Check if we've already detected this fault recently
        if self._is_duplicate_fault(fault):
            return
        
        # Add to fault history
        self.detected_faults.append(fault)
        if len(self.detected_faults) > self.max_fault_history:
            self.detected_faults = self.detected_faults[-self.max_fault_history:]
        
        # Log the fault with detailed explanation
        fault_type = fault.get('type', 'unknown')
        service = fault.get('service', 'unknown')
        message = fault.get('message', 'No message')
        
        logger.warning("="*70)
        logger.warning(f"🚨 FAULT DETECTED")
        logger.warning("="*70)
        logger.warning(f"Type: {fault_type}")
        logger.warning(f"Service: {service}")
        logger.warning(f"Severity: {fault.get('severity', 'unknown')}")
        logger.warning(f"Message: {message}")
        logger.warning(f"Timestamp: {fault.get('timestamp', 'unknown')}")
        logger.warning("="*70)
        
        # Print to console for visibility
        print(f"\n{'='*70}")
        print(f"🚨 FAULT DETECTED: {fault_type.upper()}")
        print(f"{'='*70}")
        print(f"Service: {service}")
        print(f"Severity: {fault.get('severity', 'unknown').upper()}")
        print(f"Issue: {message}")
        print(f"Time: {fault.get('timestamp', 'unknown')}")
        print(f"{'='*70}\n")
        
        # Send Discord notification for service crashes
        if fault['type'] == 'service_crash':
            self._send_discord_notification(fault)
        
        # Emit event for dashboard
        if self.event_emitter:
            try:
                self.event_emitter({
                    'event_type': 'fault_detected',
                    'fault': fault,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error emitting fault event: {e}")
    
    def _is_duplicate_fault(self, fault: Dict[str, Any]) -> bool:
        """
        Check if this fault was already detected recently (within last 5 minutes)
        
        Args:
            fault: Fault to check
            
        Returns:
            True if duplicate, False otherwise
        """
        fault_key = f"{fault['type']}:{fault.get('service', fault.get('message', ''))}"
        current_time = datetime.now()
        
        for existing_fault in self.detected_faults[-20:]:  # Check last 20 faults
            existing_key = f"{existing_fault['type']}:{existing_fault.get('service', existing_fault.get('message', ''))}"
            
            if existing_key == fault_key:
                # Check if within 5 minutes
                existing_time = datetime.fromisoformat(existing_fault['timestamp'])
                time_diff = (current_time - existing_time).total_seconds()
                
                if time_diff < 300:  # 5 minutes
                    return True
        
        return False
    
    def _send_discord_notification(self, fault: Dict[str, Any]):
        """
        Send Discord notification for service crash
        
        Args:
            fault: Fault information
        """
        if not self.discord_notifier:
            return
        
        try:
            service_name = fault.get('service', 'Unknown Service')
            status = fault.get('status', 'unknown')
            restart_count = fault.get('restart_count', 0)
            
            embed_data = {
                'title': '🚨 Service Crash Detected',
                'description': f"**Service:** {service_name}\n**Status:** {status}\n**Restart Count:** {restart_count}",
                'color': 15158332,  # Red
                'fields': [
                    {
                        'name': 'Fault Type',
                        'value': fault.get('type', 'unknown'),
                        'inline': True
                    },
                    {
                        'name': 'Severity',
                        'value': fault.get('severity', 'unknown'),
                        'inline': True
                    },
                    {
                        'name': 'Timestamp',
                        'value': fault.get('timestamp', 'unknown'),
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Auto-Detection System'
                }
            }
            
            self.discord_notifier(
                f"🚨 Service Crash: {service_name}",
                'critical',
                embed_data
            )
            
            logger.info(f"Discord notification sent for service crash: {service_name}")
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
    
    def get_detected_faults(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recently detected faults
        
        Args:
            limit: Maximum number of faults to return
            
        Returns:
            List of detected faults
        """
        return self.detected_faults[-limit:]
    
    def get_fault_statistics(self) -> Dict[str, Any]:
        """
        Get fault detection statistics
        
        Returns:
            Dictionary with statistics
        """
        total_faults = len(self.detected_faults)
        
        # Count by type
        fault_types = {}
        for fault in self.detected_faults:
            fault_type = fault.get('type', 'unknown')
            fault_types[fault_type] = fault_types.get(fault_type, 0) + 1
        
        # Count by severity
        severities = {}
        for fault in self.detected_faults:
            severity = fault.get('severity', 'unknown')
            severities[severity] = severities.get(severity, 0) + 1
        
        return {
            'total_faults': total_faults,
            'faults_by_type': fault_types,
            'faults_by_severity': severities,
            'monitoring_active': self.running,
            'last_check': datetime.now().isoformat() if self.detected_faults else None
        }


# Singleton instance
_fault_detector_instance = None

def initialize_fault_detector(discord_notifier: Callable = None, event_emitter: Callable = None) -> FaultDetector:
    """Initialize the fault detector"""
    global _fault_detector_instance
    
    if _fault_detector_instance is None:
        _fault_detector_instance = FaultDetector(
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        logger.info("Fault detector initialized")
    
    return _fault_detector_instance

def get_fault_detector() -> Optional[FaultDetector]:
    """Get the fault detector instance"""
    return _fault_detector_instance

