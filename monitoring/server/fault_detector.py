"""
Fault Detector - Real-time Fault Detection Engine
Detects system faults, container crashes, resource exhaustion, and network issues
"""

import logging
import threading
import time
import socket
import subprocess
import requests
import psutil
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
        
        # Service ports to check - Actual Heal-X-Bot services
        self.service_ports = {
            'healing-dashboard': 5001,    # Healing Dashboard API
            'monitoring-server': 5000,    # Main Monitoring Server
            'ddos-model': 8080,           # ML DDoS Detection Model
            'nginx-container': 80,        # Nginx Web Server Container
            'mysql-container': 3306       # MySQL Database Container
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
        
        # 4. Detect failed systemd services (Ubuntu server)
        service_faults = self.detect_failed_services()
        faults.extend(service_faults)
        
        # 5. Detect disk pressure (partitions >90% full)
        disk_faults = self.detect_disk_pressure()
        faults.extend(disk_faults)
        
        # 6. Detect memory pressure (high RAM + swap usage)
        memory_faults = self.detect_memory_pressure()
        faults.extend(memory_faults)
        
        # 7. Detect network interface issues
        interface_faults = self.detect_network_interface_issues()
        faults.extend(interface_faults)
        
        return faults
    
    def detect_container_crashes(self) -> List[Dict[str, Any]]:
        """
        Detect crashed or stopped containers (excluding cloud-sim containers)
        
        Returns:
            List of container crash faults
        """
        faults = []
        crashed_containers = self.container_monitor.detect_crashed_containers()
        
        for container_info in crashed_containers:
            container_name = container_info.get('container', '')
            
            # Filter out cloud-sim containers
            if container_name.startswith('cloud-sim'):
                continue
            
            fault = {
                'type': 'service_crash',
                'severity': 'critical',
                'service': container_name,
                'status': container_info.get('status', 'unknown'),
                'state': container_info.get('state', 'unknown'),
                'restart_count': container_info.get('restart_count', 0),
                'message': f"Service {container_name} has crashed or stopped",
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
            # Extract resource type from fault type
            fault_type = anomaly.get('type', 'resource_exhaustion')
            resource_name = fault_type.replace('_exhaustion', '').replace('_full', '').upper()
            
            fault = {
                'type': fault_type,
                'severity': anomaly['severity'],
                'service': resource_name,  # CPU, MEMORY, or DISK
                'resource': resource_name,
                'message': anomaly['message'],
                'description': anomaly['message'],
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
                message = f"Service {service_name} is not reachable on port {port}"
                fault = {
                    'type': 'network_issue',
                    'severity': 'high',
                    'service': service_name,
                    'resource': service_name,
                    'port': port,
                    'message': message,
                    'description': message,
                    'timestamp': datetime.now().isoformat()
                }
                faults.append(fault)
        
        return faults
    
    def detect_failed_services(self) -> List[Dict[str, Any]]:
        """
        Detect failed systemd services on Ubuntu server
        
        Returns:
            List of failed service faults
        """
        faults = []
        
        try:
            # Run systemctl --failed to get failed services
            result = subprocess.run(
                ['systemctl', '--failed', '--no-pager', '--plain'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header and summary lines
                for line in lines:
                    # Parse lines like: nginx.service loaded failed failed NGINX
                    if '.service' in line and 'failed' in line.lower():
                        parts = line.split()
                        if len(parts) >= 1:
                            service_name = parts[0].replace('.service', '')
                            
                            fault = {
                                'type': 'service_failed',
                                'severity': 'critical',
                                'service': service_name,
                                'resource': 'systemd',
                                'message': f"Systemd service {service_name} has failed",
                                'description': f"Service {service_name} is in failed state. Run 'systemctl status {service_name}' for details.",
                                'timestamp': datetime.now().isoformat(),
                                'details': {'raw_line': line}
                            }
                            faults.append(fault)
                            
        except subprocess.TimeoutExpired:
            logger.warning("Timeout checking failed services")
        except FileNotFoundError:
            logger.debug("systemctl not available (not a systemd system)")
        except Exception as e:
            logger.error(f"Error detecting failed services: {e}")
        
        return faults
    
    def detect_disk_pressure(self) -> List[Dict[str, Any]]:
        """
        Detect disk partitions with high usage (>90%)
        
        Returns:
            List of disk pressure faults
        """
        faults = []
        
        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions(all=False)
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    percent_used = usage.percent
                    
                    # Critical if >95%, high if >90%
                    if percent_used >= 95:
                        severity = 'critical'
                    elif percent_used >= 90:
                        severity = 'high'
                    else:
                        continue
                    
                    free_gb = usage.free / (1024**3)
                    total_gb = usage.total / (1024**3)
                    
                    fault = {
                        'type': 'disk_pressure',
                        'severity': severity,
                        'service': 'DISK',
                        'resource': partition.mountpoint,
                        'message': f"Disk {partition.mountpoint} is {percent_used:.1f}% full ({free_gb:.1f}GB free)",
                        'description': f"Partition {partition.device} mounted at {partition.mountpoint} has low free space.",
                        'value': percent_used,
                        'threshold': 90,
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'device': partition.device,
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_gb': round(total_gb, 2),
                            'free_gb': round(free_gb, 2),
                            'percent_used': round(percent_used, 1)
                        }
                    }
                    faults.append(fault)
                    
                except PermissionError:
                    continue
                except Exception as e:
                    logger.debug(f"Error checking disk {partition.mountpoint}: {e}")
                    
        except Exception as e:
            logger.error(f"Error detecting disk pressure: {e}")
        
        return faults
    
    def detect_memory_pressure(self) -> List[Dict[str, Any]]:
        """
        Detect high memory and swap usage
        
        Returns:
            List of memory pressure faults
        """
        faults = []
        
        try:
            # Check virtual memory (RAM)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Memory critical if >95%, warning if >90%
            if mem.percent >= 95:
                fault = {
                    'type': 'memory_critical',
                    'severity': 'critical',
                    'service': 'MEMORY',
                    'resource': 'RAM',
                    'message': f"Memory usage critical: {mem.percent:.1f}% ({mem.available / (1024**3):.1f}GB available)",
                    'description': "System memory is nearly exhausted. Consider killing processes or adding RAM.",
                    'value': mem.percent,
                    'threshold': 95,
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'total_gb': round(mem.total / (1024**3), 2),
                        'available_gb': round(mem.available / (1024**3), 2),
                        'percent_used': round(mem.percent, 1),
                        'swap_percent': round(swap.percent, 1)
                    }
                }
                faults.append(fault)
            elif mem.percent >= 90:
                fault = {
                    'type': 'memory_pressure',
                    'severity': 'high',
                    'service': 'MEMORY',
                    'resource': 'RAM',
                    'message': f"Memory usage high: {mem.percent:.1f}% ({mem.available / (1024**3):.1f}GB available)",
                    'description': "System memory usage is elevated. Monitor for further increase.",
                    'value': mem.percent,
                    'threshold': 90,
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'total_gb': round(mem.total / (1024**3), 2),
                        'available_gb': round(mem.available / (1024**3), 2),
                        'percent_used': round(mem.percent, 1),
                        'swap_percent': round(swap.percent, 1)
                    }
                }
                faults.append(fault)
            
            # Check swap usage - high swap indicates memory pressure
            if swap.total > 0 and swap.percent >= 80:
                fault = {
                    'type': 'swap_pressure',
                    'severity': 'warning',
                    'service': 'MEMORY',
                    'resource': 'SWAP',
                    'message': f"Swap usage high: {swap.percent:.1f}% ({swap.used / (1024**3):.2f}GB used)",
                    'description': "High swap usage indicates memory pressure. System may be slow.",
                    'value': swap.percent,
                    'threshold': 80,
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'swap_total_gb': round(swap.total / (1024**3), 2),
                        'swap_used_gb': round(swap.used / (1024**3), 2),
                        'swap_percent': round(swap.percent, 1)
                    }
                }
                faults.append(fault)
                
        except Exception as e:
            logger.error(f"Error detecting memory pressure: {e}")
        
        return faults
    
    def detect_network_interface_issues(self) -> List[Dict[str, Any]]:
        """
        Detect network interface issues (interfaces down or with errors)
        
        Returns:
            List of network interface faults
        """
        faults = []
        
        try:
            # Get network interface stats
            net_if_stats = psutil.net_if_stats()
            net_io = psutil.net_io_counters(pernic=True)
            
            for iface, stats in net_if_stats.items():
                # Skip loopback
                if iface.lower() in ['lo', 'loopback']:
                    continue
                
                # Check if interface is down
                if not stats.isup:
                    fault = {
                        'type': 'network_interface_down',
                        'severity': 'high',
                        'service': 'NETWORK',
                        'resource': iface,
                        'message': f"Network interface {iface} is DOWN",
                        'description': f"Interface {iface} is not operational. Check cable or network configuration.",
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'interface': iface,
                            'speed': stats.speed,
                            'mtu': stats.mtu,
                            'isup': stats.isup
                        }
                    }
                    faults.append(fault)
                
                # Check for high error rates
                if iface in net_io:
                    io = net_io[iface]
                    total_packets = io.packets_sent + io.packets_recv
                    total_errors = io.errin + io.errout
                    
                    if total_packets > 1000 and total_errors > 0:
                        error_rate = (total_errors / total_packets) * 100
                        if error_rate > 1:  # More than 1% error rate
                            fault = {
                                'type': 'network_interface_errors',
                                'severity': 'warning',
                                'service': 'NETWORK',
                                'resource': iface,
                                'message': f"Network interface {iface} has high error rate: {error_rate:.2f}%",
                                'description': f"Interface {iface} is experiencing packet errors. Check for hardware or cable issues.",
                                'value': error_rate,
                                'threshold': 1,
                                'timestamp': datetime.now().isoformat(),
                                'details': {
                                    'interface': iface,
                                    'errors_in': io.errin,
                                    'errors_out': io.errout,
                                    'packets_sent': io.packets_sent,
                                    'packets_recv': io.packets_recv
                                }
                            }
                            faults.append(fault)
                            
        except Exception as e:
            logger.error(f"Error detecting network interface issues: {e}")
        
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
            if port in [80, 8081, 8082]:
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
        
        # Send Discord notification for all faults
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
            fault_type = fault.get('type', 'Unknown Fault')
            message = fault.get('message', 'No details provided')
            severity = fault.get('severity', 'warning')
            timestamp = fault.get('timestamp', datetime.now().isoformat())
            
            # customized title and color based on severity
            if severity == 'critical':
                color = 15158332 # Red
                title = f'🚨 Critical Issue: {service_name}'
            elif severity == 'high':
                color = 15105570 # Orange
                title = f'⚠️ High Priority Issue: {service_name}'
            else:
                color = 16776960 # Yellow
                title = f'⚠️ Issue Detected: {service_name}'

            embed_data = {
                'title': title,
                'description': f"**Type:** {fault_type}\n**Message:** {message}",
                'color': color,
                'fields': [
                    {
                        'name': 'Service',
                        'value': service_name,
                        'inline': True
                    },
                    {
                        'name': 'Severity',
                        'value': severity.upper(),
                        'inline': True
                    },
                    {
                        'name': 'Details',
                        'value': str(fault.get('details', 'N/A'))[:200], # Truncate if too long
                        'inline': False
                    },
                    {
                        'name': 'Timestamp',
                        'value': timestamp,
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Auto-Detection System'
                }
            }
            
            self.discord_notifier(
                f"🚨 Alert: {fault_type} on {service_name}",
                severity,
                embed_data
            )
            
            logger.info(f"Discord notification sent for fault: {fault_type} on {service_name}")
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

