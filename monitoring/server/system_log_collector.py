"""
System-Wide Log Collector for Ubuntu
Collects logs from system services (Docker, Apache, systemd, syslog, etc.)
"""

import os
import subprocess
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
import threading
import time

logger = logging.getLogger(__name__)

class SystemLogCollector:
    """Collects and parses logs from system-wide services"""
    
    def __init__(self):
        self.log_sources = {
            'docker': {'enabled': True, 'parser': self.parse_docker_logs},
            'syslog': {'enabled': True, 'parser': self.parse_syslog},
            'auth': {'enabled': True, 'parser': self.parse_auth_log},
            'kern': {'enabled': True, 'parser': self.parse_kern_log},
            'systemd': {'enabled': True, 'parser': self.parse_systemd_journal},
            'apache': {'enabled': True, 'parser': self.parse_apache_logs},
            'nginx': {'enabled': True, 'parser': self.parse_nginx_logs},
        }
        
        self.collected_logs = []
        self.max_logs = 1000  # Reduced from 10,000 to 1,000 to save memory
        self.last_collection_time = {}
        self.running = False
        self.collection_thread = None
        self.total_logs_collected = 0  # Counter for statistics
        
    def start_collection(self, interval_seconds: int = 30):
        """Start continuous log collection"""
        self.running = True
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.collection_thread.start()
        logger.info(f"System log collection started (interval: {interval_seconds}s)")
        
    def stop_collection(self):
        """Stop log collection"""
        self.running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        logger.info("System log collection stopped")
        
    def _collection_loop(self, interval_seconds: int):
        """Continuous collection loop"""
        while self.running:
            try:
                self.collect_all_logs()
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
            time.sleep(interval_seconds)
            
    def collect_all_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from all enabled sources"""
        new_logs = []
        
        for source_name, config in self.log_sources.items():
            if config['enabled']:
                try:
                    source_logs = config['parser']()
                    new_logs.extend(source_logs)
                except Exception as e:
                    logger.error(f"Error collecting {source_name} logs: {e}")
        
        # Update total counter
        self.total_logs_collected += len(new_logs)
        
        # Add to collected logs and maintain size limit (keep only recent logs)
        self.collected_logs.extend(new_logs)
        if len(self.collected_logs) > self.max_logs:
            # Remove oldest logs to maintain limit
            excess = len(self.collected_logs) - self.max_logs
            self.collected_logs = self.collected_logs[excess:]
            
        return new_logs
    
    def parse_docker_logs(self) -> List[Dict[str, Any]]:
        """Collect logs from Docker containers"""
        logs = []
        
        try:
            # Get list of running containers
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return logs
                
            containers = result.stdout.strip().split('\n')
            
            # Get logs from each container (last 10 lines to reduce data)
            for container in containers:
                if not container:
                    continue
                    
                try:
                    log_result = subprocess.run(
                        ['docker', 'logs', '--tail', '10', '--timestamps', container],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if log_result.returncode == 0:
                        for line in log_result.stdout.split('\n'):
                            if line.strip():
                                parsed = self._parse_docker_log_line(line, container)
                                if parsed:
                                    logs.append(parsed)
                                    
                except Exception as e:
                    logger.debug(f"Error getting logs from container {container}: {e}")
                    
        except Exception as e:
            logger.debug(f"Docker not available or error: {e}")
            
        return logs
    
    def _parse_docker_log_line(self, line: str, container: str) -> Optional[Dict[str, Any]]:
        """Parse a single Docker log line"""
        try:
            # Docker format: 2024-10-29T12:00:00.000000000Z log message
            match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z?)\s+(.*)', line)
            
            if match:
                timestamp_str, message = match.groups()
                
                # Determine log level
                level = self._detect_log_level(message)
                
                return {
                    'timestamp': timestamp_str,
                    'service': f'docker-{container}',
                    'level': level,
                    'message': message.strip(),
                    'source': 'docker',
                    'container': container
                }
        except Exception as e:
            logger.debug(f"Error parsing Docker log line: {e}")
            
        return None
    
    def parse_syslog(self) -> List[Dict[str, Any]]:
        """Parse system syslog"""
        logs = []
        syslog_path = '/var/log/syslog'
        
        try:
            # Get last read position
            last_time = self.last_collection_time.get('syslog', datetime.now() - timedelta(minutes=5))
            
            with open(syslog_path, 'r') as f:
                for line in f:
                    parsed = self._parse_syslog_line(line)
                    if parsed and self._is_recent(parsed['timestamp'], last_time):
                        logs.append(parsed)
                        
            self.last_collection_time['syslog'] = datetime.now()
            
        except PermissionError:
            logger.debug("No permission to read syslog - run with sudo or add user to adm group")
        except FileNotFoundError:
            logger.debug("Syslog file not found")
        except Exception as e:
            logger.error(f"Error parsing syslog: {e}")
            
        return logs
    
    def _parse_syslog_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse syslog line"""
        try:
            # Format: Oct 29 12:00:00 hostname service[pid]: message
            match = re.match(
                r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:\[]+)(?:\[(\d+)\])?:\s+(.*)',
                line
            )
            
            if match:
                timestamp_str, hostname, service, pid, message = match.groups()
                
                # Convert to ISO format
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
                
                level = self._detect_log_level(message)
                
                return {
                    'timestamp': timestamp.isoformat(),
                    'service': f'syslog-{service}',
                    'level': level,
                    'message': message.strip(),
                    'source': 'syslog',
                    'hostname': hostname,
                    'pid': pid
                }
        except Exception as e:
            logger.debug(f"Error parsing syslog line: {e}")
            
        return None
    
    def parse_auth_log(self) -> List[Dict[str, Any]]:
        """Parse authentication logs"""
        logs = []
        auth_log_path = '/var/log/auth.log'
        
        try:
            last_time = self.last_collection_time.get('auth', datetime.now() - timedelta(minutes=5))
            
            with open(auth_log_path, 'r') as f:
                for line in f:
                    parsed = self._parse_auth_log_line(line)
                    if parsed and self._is_recent(parsed['timestamp'], last_time):
                        logs.append(parsed)
                        
            self.last_collection_time['auth'] = datetime.now()
            
        except PermissionError:
            logger.debug("No permission to read auth.log - run with sudo or add user to adm group")
        except FileNotFoundError:
            logger.debug("Auth log file not found")
        except Exception as e:
            logger.error(f"Error parsing auth.log: {e}")
            
        return logs
    
    def _parse_auth_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse auth.log line"""
        try:
            # Similar format to syslog
            match = re.match(
                r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:\[]+)(?:\[(\d+)\])?:\s+(.*)',
                line
            )
            
            if match:
                timestamp_str, hostname, service, pid, message = match.groups()
                
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
                
                # Auth logs are often WARNING or ERROR level
                level = 'WARNING' if any(keyword in message.lower() for keyword in ['failed', 'invalid', 'unauthorized']) else 'INFO'
                
                return {
                    'timestamp': timestamp.isoformat(),
                    'service': f'auth-{service}',
                    'level': level,
                    'message': message.strip(),
                    'source': 'auth',
                    'hostname': hostname,
                    'pid': pid
                }
        except Exception as e:
            logger.debug(f"Error parsing auth.log line: {e}")
            
        return None
    
    def parse_kern_log(self) -> List[Dict[str, Any]]:
        """Parse kernel logs"""
        logs = []
        kern_log_path = '/var/log/kern.log'
        
        try:
            last_time = self.last_collection_time.get('kern', datetime.now() - timedelta(minutes=5))
            
            if os.path.exists(kern_log_path):
                with open(kern_log_path, 'r') as f:
                    for line in f:
                        parsed = self._parse_kern_log_line(line)
                        if parsed and self._is_recent(parsed['timestamp'], last_time):
                            logs.append(parsed)
                            
                self.last_collection_time['kern'] = datetime.now()
            
        except PermissionError:
            logger.debug("No permission to read kern.log")
        except Exception as e:
            logger.error(f"Error parsing kern.log: {e}")
            
        return logs
    
    def _parse_kern_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse kern.log line"""
        try:
            match = re.match(
                r'(\w+\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+kernel:\s+\[[\s\d.]+\]\s+(.*)',
                line
            )
            
            if match:
                timestamp_str, hostname, message = match.groups()
                
                current_year = datetime.now().year
                timestamp = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
                
                level = self._detect_log_level(message)
                
                return {
                    'timestamp': timestamp.isoformat(),
                    'service': 'kernel',
                    'level': level,
                    'message': message.strip(),
                    'source': 'kernel',
                    'hostname': hostname
                }
        except Exception as e:
            logger.debug(f"Error parsing kern.log line: {e}")
            
        return None
    
    def parse_systemd_journal(self) -> List[Dict[str, Any]]:
        """Parse systemd journal logs"""
        logs = []
        
        try:
            # Get only recent logs (last 20 entries to reduce data)
            result = subprocess.run(
                ['journalctl', '-n', '20', '--output=json', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            parsed = self._parse_systemd_journal_entry(entry)
                            if parsed:
                                logs.append(parsed)
                        except json.JSONDecodeError:
                            continue
                            
        except subprocess.TimeoutExpired:
            logger.debug("Journalctl timeout")
        except FileNotFoundError:
            logger.debug("journalctl not available")
        except Exception as e:
            logger.debug(f"Error reading systemd journal: {e}")
            
        return logs
    
    def _parse_systemd_journal_entry(self, entry: Dict) -> Optional[Dict[str, Any]]:
        """Parse systemd journal entry"""
        try:
            # Convert microseconds timestamp to datetime
            timestamp_us = int(entry.get('__REALTIME_TIMESTAMP', 0))
            timestamp = datetime.fromtimestamp(timestamp_us / 1000000)
            
            message = entry.get('MESSAGE', '')
            unit = entry.get('_SYSTEMD_UNIT', entry.get('SYSLOG_IDENTIFIER', 'unknown'))
            priority = int(entry.get('PRIORITY', 6))
            
            # Convert syslog priority to level
            if priority <= 3:
                level = 'ERROR'
            elif priority <= 4:
                level = 'WARNING'
            else:
                level = 'INFO'
            
            return {
                'timestamp': timestamp.isoformat(),
                'service': f'systemd-{unit}',
                'level': level,
                'message': message,
                'source': 'systemd',
                'priority': priority
            }
        except Exception as e:
            logger.debug(f"Error parsing systemd entry: {e}")
            
        return None
    
    def parse_apache_logs(self) -> List[Dict[str, Any]]:
        """Parse Apache access and error logs"""
        logs = []
        apache_error_log = '/var/log/apache2/error.log'
        
        try:
            if os.path.exists(apache_error_log):
                last_time = self.last_collection_time.get('apache', datetime.now() - timedelta(minutes=5))
                
                with open(apache_error_log, 'r') as f:
                    for line in f:
                        parsed = self._parse_apache_error_line(line)
                        if parsed and self._is_recent(parsed['timestamp'], last_time):
                            logs.append(parsed)
                            
                self.last_collection_time['apache'] = datetime.now()
                
        except PermissionError:
            logger.debug("No permission to read Apache logs")
        except Exception as e:
            logger.debug(f"Apache logs not available: {e}")
            
        return logs
    
    def _parse_apache_error_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse Apache error log line"""
        try:
            # Format: [Day Mon DD HH:MM:SS.mmmmmm YYYY] [level] message
            match = re.match(
                r'\[(\w+\s+\w+\s+\d+\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d{4})\]\s+\[([^\]]+)\]\s+(.*)',
                line
            )
            
            if match:
                timestamp_str, level, message = match.groups()
                
                # Parse timestamp
                timestamp = datetime.strptime(timestamp_str.split('.')[0], "%a %b %d %H:%M:%S %Y")
                
                return {
                    'timestamp': timestamp.isoformat(),
                    'service': 'apache',
                    'level': level.upper().split(':')[0],
                    'message': message.strip(),
                    'source': 'apache'
                }
        except Exception as e:
            logger.debug(f"Error parsing Apache log line: {e}")
            
        return None
    
    def parse_nginx_logs(self) -> List[Dict[str, Any]]:
        """Parse Nginx error logs"""
        logs = []
        nginx_error_log = '/var/log/nginx/error.log'
        
        try:
            if os.path.exists(nginx_error_log):
                last_time = self.last_collection_time.get('nginx', datetime.now() - timedelta(minutes=5))
                
                with open(nginx_error_log, 'r') as f:
                    for line in f:
                        parsed = self._parse_nginx_error_line(line)
                        if parsed and self._is_recent(parsed['timestamp'], last_time):
                            logs.append(parsed)
                            
                self.last_collection_time['nginx'] = datetime.now()
                
        except PermissionError:
            logger.debug("No permission to read Nginx logs")
        except Exception as e:
            logger.debug(f"Nginx logs not available: {e}")
            
        return logs
    
    def _parse_nginx_error_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse Nginx error log line"""
        try:
            # Format: YYYY/MM/DD HH:MM:SS [level] pid#tid: *cid message
            match = re.match(
                r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[([^\]]+)\]\s+\d+#\d+:\s+(.*)',
                line
            )
            
            if match:
                timestamp_str, level, message = match.groups()
                
                timestamp = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
                
                return {
                    'timestamp': timestamp.isoformat(),
                    'service': 'nginx',
                    'level': level.upper(),
                    'message': message.strip(),
                    'source': 'nginx'
                }
        except Exception as e:
            logger.debug(f"Error parsing Nginx log line: {e}")
            
        return None
    
    def _detect_log_level(self, message: str) -> str:
        """Detect log level from message content"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['error', 'fail', 'exception', 'critical', 'fatal']):
            return 'ERROR'
        elif any(keyword in message_lower for keyword in ['warn', 'warning']):
            return 'WARNING'
        elif any(keyword in message_lower for keyword in ['debug']):
            return 'DEBUG'
        else:
            return 'INFO'
    
    def _is_recent(self, timestamp_str: str, since: datetime) -> bool:
        """Check if timestamp is more recent than given datetime"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return timestamp.replace(tzinfo=None) >= since
        except Exception:
            return True  # Include if we can't parse
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None, 
                       source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent collected logs with optional filtering"""
        filtered_logs = self.collected_logs
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.get('level') == level.upper()]
            
        if source:
            filtered_logs = [log for log in filtered_logs if log.get('source') == source]
        
        # Sort by timestamp (newest first)
        sorted_logs = sorted(
            filtered_logs,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        return sorted_logs[:limit]
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected logs"""
        stats = {
            'total_logs': len(self.collected_logs),
            'by_level': {},
            'by_source': {},
            'by_service': {}
        }
        
        for log in self.collected_logs:
            # Count by level
            level = log.get('level', 'UNKNOWN')
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
            # Count by source
            source = log.get('source', 'unknown')
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
            
            # Count by service
            service = log.get('service', 'unknown')
            stats['by_service'][service] = stats['by_service'].get(service, 0) + 1
        
        return stats
    
    def inject_test_log(self, service: str, message: str, level: str = "ERROR", 
                       source: str = "test") -> Dict[str, Any]:
        """
        Inject a test log entry (for testing/demonstration purposes)
        
        Args:
            service: Service name (e.g., 'systemd-resolved', 'docker')
            message: Log message
            level: Log level (ERROR, WARNING, INFO, etc.)
            source: Log source (test, systemd, docker, etc.)
        
        Returns:
            The created log entry
        """
        test_log = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'message': message,
            'level': level.upper(),
            'source': source,
            'source_file': f'/var/log/{source}_test.log'
        }
        
        # Add to collected logs
        self.collected_logs.append(test_log)
        self.total_logs_collected += 1
        
        # Maintain size limit
        if len(self.collected_logs) > self.max_logs:
            excess = len(self.collected_logs) - self.max_logs
            self.collected_logs = self.collected_logs[excess:]
        
        logger.info(f"Injected test log: {service} - {level} - {message[:50]}...")
        return test_log


# Singleton instance
_system_collector_instance = None

def initialize_system_log_collector():
    """Initialize the system log collector"""
    global _system_collector_instance
    
    if _system_collector_instance is None:
        _system_collector_instance = SystemLogCollector()
        _system_collector_instance.start_collection(interval_seconds=30)
        logger.info("System log collector initialized and started")
    
    return _system_collector_instance

def get_system_log_collector():
    """Get the system log collector instance"""
    return _system_collector_instance


if __name__ == "__main__":
    # Test the collector
    logging.basicConfig(level=logging.INFO)
    
    collector = SystemLogCollector()
    
    print("🔍 Collecting system logs...")
    logs = collector.collect_all_logs()
    
    print(f"\n✅ Collected {len(logs)} log entries\n")
    
    # Show statistics
    stats = collector.get_log_statistics()
    print("📊 Statistics:")
    print(f"   Total logs: {stats['total_logs']}")
    print(f"   By level: {stats['by_level']}")
    print(f"   By source: {stats['by_source']}")
    
    # Show recent ERROR logs
    print("\n🚨 Recent ERROR logs:")
    error_logs = collector.get_recent_logs(limit=5, level='ERROR')
    for log in error_logs:
        print(f"   [{log['timestamp']}] {log['service']}: {log['message'][:80]}")

