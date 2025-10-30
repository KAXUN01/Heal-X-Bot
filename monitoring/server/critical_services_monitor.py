"""
Critical Services Monitor for Ubuntu
Monitors essential system services and their logs
"""

import subprocess
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import threading
import time

logger = logging.getLogger(__name__)

class CriticalServicesMonitor:
    """Monitor critical system services and collect their logs"""
    
    def __init__(self):
        # Define critical services by category
        self.critical_services = {
            'CRITICAL': {
                'docker': 'Docker container runtime - manages all containers',
                'containerd': 'Container runtime - critical for Docker',
                'systemd-journald': 'System logging daemon - core logging',
                'systemd-logind': 'Login manager - handles user sessions',
                'dbus': 'Message bus - inter-process communication',
            },
            'IMPORTANT': {
                'cron': 'Task scheduler - runs scheduled jobs',
                'rsyslog': 'System logger - handles syslog messages',
                'systemd-resolved': 'DNS resolver - network name resolution',
                'systemd-udevd': 'Device manager - hardware management',
            },
            'SECURITY': {
                'snapd': 'Snap package manager',
                'ufw': 'Firewall manager',
                'fail2ban': 'Intrusion prevention',
                'apparmor': 'Mandatory access control',
            }
        }
        
        self.service_logs = []
        self.max_logs = 500  # Keep last 500 logs per category
        self.running = False
        self.collection_thread = None
        
        # Track service status
        self.service_status = {}
        
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring"""
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.collection_thread.start()
        logger.info(f"Critical services monitoring started (interval: {interval_seconds}s)")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("Critical services monitoring stopped")
        
    def _monitoring_loop(self, interval_seconds: int):
        """Continuous monitoring loop"""
        while self.running:
            try:
                self.collect_all_service_logs()
                self.check_service_status()
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            time.sleep(interval_seconds)
            
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_active = result.stdout.strip() == 'active'
            
            # Get detailed status
            status_result = subprocess.run(
                ['systemctl', 'status', service_name, '--no-pager', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                'service': service_name,
                'active': is_active,
                'status': 'active' if is_active else 'inactive',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Error getting status for {service_name}: {e}")
            return {
                'service': service_name,
                'active': False,
                'status': 'unknown',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_service_status(self):
        """Check status of all critical services"""
        for category, services in self.critical_services.items():
            for service_name in services.keys():
                status = self.get_service_status(service_name)
                self.service_status[service_name] = status
                
                # Log if service is not active
                if not status['active'] and category in ['CRITICAL', 'IMPORTANT']:
                    logger.warning(f"Critical service {service_name} is not active!")
    
    def collect_service_logs(self, service_name: str, category: str, lines: int = 20) -> List[Dict[str, Any]]:
        """Collect logs for a specific service"""
        logs = []
        
        try:
            # Get recent logs from journalctl
            result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', str(lines), '--output=json', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            parsed = self._parse_journal_entry(entry, service_name, category)
                            if parsed:
                                logs.append(parsed)
                        except json.JSONDecodeError:
                            continue
                            
        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout collecting logs for {service_name}")
        except Exception as e:
            logger.debug(f"Error collecting logs for {service_name}: {e}")
            
        return logs
    
    def _parse_journal_entry(self, entry: Dict, service_name: str, category: str) -> Optional[Dict[str, Any]]:
        """Parse systemd journal entry"""
        try:
            # Convert microseconds timestamp to datetime
            timestamp_us = int(entry.get('__REALTIME_TIMESTAMP', 0))
            timestamp = datetime.fromtimestamp(timestamp_us / 1000000)
            
            message = entry.get('MESSAGE', '')
            priority = int(entry.get('PRIORITY', 6))
            
            # Convert syslog priority to level
            if priority <= 3:
                level = 'ERROR'
            elif priority <= 4:
                level = 'WARNING'
            elif priority == 5:
                level = 'NOTICE'
            else:
                level = 'INFO'
            
            # Get service description
            description = ''
            for cat, services in self.critical_services.items():
                if service_name in services:
                    description = services[service_name]
                    break
            
            return {
                'timestamp': timestamp.isoformat(),
                'service': service_name,
                'category': category,
                'level': level,
                'priority': priority,
                'message': message,
                'description': description,
                'source': 'systemd-journal'
            }
        except Exception as e:
            logger.debug(f"Error parsing journal entry: {e}")
            return None
    
    def collect_all_service_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from all critical services"""
        new_logs = []
        
        for category, services in self.critical_services.items():
            for service_name in services.keys():
                try:
                    service_logs = self.collect_service_logs(service_name, category, lines=10)
                    new_logs.extend(service_logs)
                except Exception as e:
                    logger.error(f"Error collecting logs for {service_name}: {e}")
        
        # Add to collected logs and maintain size limit
        self.service_logs.extend(new_logs)
        if len(self.service_logs) > self.max_logs:
            excess = len(self.service_logs) - self.max_logs
            self.service_logs = self.service_logs[excess:]
            
        return new_logs
    
    def get_logs_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs filtered by category"""
        filtered = [log for log in self.service_logs if log.get('category') == category]
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(
            filtered,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_logs[:limit]
    
    def get_logs_by_service(self, service_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific service"""
        filtered = [log for log in self.service_logs if log.get('service') == service_name]
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(
            filtered,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_logs[:limit]
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent logs with optional level filter"""
        filtered = self.service_logs
        
        if level:
            filtered = [log for log in filtered if log.get('level') == level.upper()]
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(
            filtered,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_logs[:limit]
    
    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Get critical issues (errors from CRITICAL category services)"""
        issues = []
        
        for log in self.service_logs:
            if (log.get('category') == 'CRITICAL' and 
                log.get('level') in ['ERROR', 'WARNING']):
                issues.append(log)
        
        # Sort by timestamp (newest first)
        sorted_issues = sorted(
            issues,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_issues[:50]  # Return top 50 critical issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected logs"""
        stats = {
            'total_logs': len(self.service_logs),
            'by_category': {},
            'by_level': {},
            'by_service': {},
            'service_status': {}
        }
        
        for log in self.service_logs:
            # Count by category
            category = log.get('category', 'unknown')
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count by level
            level = log.get('level', 'unknown')
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            # Count by service
            service = log.get('service', 'unknown')
            stats['by_service'][service] = stats['by_service'].get(service, 0) + 1
        
        # Add service status
        for service_name, status in self.service_status.items():
            stats['service_status'][service_name] = status
        
        return stats
    
    def get_service_list(self) -> Dict[str, List[Dict[str, str]]]:
        """Get list of all monitored services by category"""
        service_list = {}
        
        for category, services in self.critical_services.items():
            service_list[category] = []
            for service_name, description in services.items():
                status = self.service_status.get(service_name, {})
                service_list[category].append({
                    'name': service_name,
                    'description': description,
                    'active': status.get('active', False),
                    'status': status.get('status', 'unknown')
                })
        
        return service_list


# Singleton instance
_critical_monitor_instance = None

def initialize_critical_services_monitor():
    """Initialize the critical services monitor"""
    global _critical_monitor_instance
    
    if _critical_monitor_instance is None:
        _critical_monitor_instance = CriticalServicesMonitor()
        _critical_monitor_instance.start_monitoring(interval_seconds=60)
        logger.info("Critical services monitor initialized and started")
    
    return _critical_monitor_instance

def get_critical_services_monitor():
    """Get the critical services monitor instance"""
    return _critical_monitor_instance


if __name__ == "__main__":
    # Test the monitor
    logging.basicConfig(level=logging.INFO)
    
    monitor = CriticalServicesMonitor()
    
    print("🔍 Collecting critical service logs...")
    logs = monitor.collect_all_service_logs()
    
    print(f"\n✅ Collected {len(logs)} log entries\n")
    
    # Show statistics
    stats = monitor.get_statistics()
    print("📊 Statistics:")
    print(f"   Total logs: {stats['total_logs']}")
    print(f"   By category: {stats['by_category']}")
    print(f"   By level: {stats['by_level']}")
    
    # Show critical issues
    print("\n🚨 Critical Issues:")
    issues = monitor.get_critical_issues()
    for issue in issues[:5]:
        print(f"   [{issue['timestamp']}] {issue['service']}: {issue['message'][:80]}")
    
    # Show service status
    print("\n📋 Service Status:")
    service_list = monitor.get_service_list()
    for category, services in service_list.items():
        print(f"\n{category}:")
        for service in services:
            status_icon = "✅" if service['active'] else "❌"
            print(f"   {status_icon} {service['name']}: {service['description']}")

