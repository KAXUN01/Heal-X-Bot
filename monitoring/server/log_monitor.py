"""
Real-time Log Monitoring and Analysis System
Monitors system logs and application logs to detect issues and anomalies
"""

import os
import re
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Any
import psutil
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogMonitor:
    """
    Real-time log monitoring system that analyzes logs for issues
    """
    
    def __init__(self):
        self.log_files = []
        self.issue_patterns = self._define_issue_patterns()
        self.detected_issues = deque(maxlen=1000)
        self.issue_stats = defaultdict(int)
        self.monitoring = False
        self.monitor_thread = None
        
        # Track file positions for continuous monitoring
        self.file_positions = {}
        
        # Issue severity levels
        self.severity_levels = {
            'CRITICAL': 5,
            'ERROR': 4,
            'WARNING': 3,
            'INFO': 2,
            'DEBUG': 1
        }
        
        # Recent issues cache (last 5 minutes)
        self.recent_issues = []
        
    def _define_issue_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Define patterns to detect various system issues
        """
        return {
            # Application Errors
            'exception': {
                'pattern': re.compile(r'(Exception|Error|Traceback|CRITICAL|FATAL)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Application Error',
                'description': 'Application exception or critical error detected',
                'auto_heal': True
            },
            
            # Database Issues
            'database_connection': {
                'pattern': re.compile(r'(database.*connection.*failed|connection.*refused|connection.*timeout|too many connections)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Database Issue',
                'description': 'Database connection problem detected',
                'auto_heal': True
            },
            
            'database_deadlock': {
                'pattern': re.compile(r'(deadlock|lock wait timeout)', re.IGNORECASE),
                'severity': 'ERROR',
                'category': 'Database Issue',
                'description': 'Database deadlock or lock timeout',
                'auto_heal': True
            },
            
            # Memory Issues
            'memory_leak': {
                'pattern': re.compile(r'(out of memory|memory leak|cannot allocate memory|MemoryError)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Memory Issue',
                'description': 'Memory allocation problem detected',
                'auto_heal': True
            },
            
            # Network Issues
            'network_timeout': {
                'pattern': re.compile(r'(connection.*timeout|request.*timeout|read.*timeout|timed out)', re.IGNORECASE),
                'severity': 'WARNING',
                'category': 'Network Issue',
                'description': 'Network timeout detected',
                'auto_heal': False
            },
            
            'port_conflict': {
                'pattern': re.compile(r'(address already in use|port.*already.*bound|bind.*failed)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Network Issue',
                'description': 'Port binding conflict',
                'auto_heal': True
            },
            
            # Security Issues
            'authentication_failure': {
                'pattern': re.compile(r'(authentication failed|unauthorized|access denied|permission denied|403 Forbidden)', re.IGNORECASE),
                'severity': 'WARNING',
                'category': 'Security Issue',
                'description': 'Authentication or authorization failure',
                'auto_heal': False
            },
            
            'ddos_attack': {
                'pattern': re.compile(r'(ddos|denial of service|too many requests|rate limit exceeded)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Security Issue',
                'description': 'Potential DDoS attack detected',
                'auto_heal': True
            },
            
            # Performance Issues
            'slow_query': {
                'pattern': re.compile(r'(slow query|query.*exceeded|execution time.*exceeded)', re.IGNORECASE),
                'severity': 'WARNING',
                'category': 'Performance Issue',
                'description': 'Slow database query detected',
                'auto_heal': False
            },
            
            'high_latency': {
                'pattern': re.compile(r'(high latency|response time.*high|slow response)', re.IGNORECASE),
                'severity': 'WARNING',
                'category': 'Performance Issue',
                'description': 'High latency or slow response detected',
                'auto_heal': False
            },
            
            # Service Issues
            'service_crash': {
                'pattern': re.compile(r'(service.*crashed|process.*terminated|service.*died|segmentation fault)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Service Issue',
                'description': 'Service crash detected',
                'auto_heal': True
            },
            
            'restart_loop': {
                'pattern': re.compile(r'(restart.*loop|too many restarts|crash.*loop)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Service Issue',
                'description': 'Service restart loop detected',
                'auto_heal': True
            },
            
            # File System Issues
            'disk_full': {
                'pattern': re.compile(r'(disk full|no space left|filesystem full)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Filesystem Issue',
                'description': 'Disk space exhausted',
                'auto_heal': True
            },
            
            'file_permission': {
                'pattern': re.compile(r'(permission denied.*file|cannot.*write|access denied.*file)', re.IGNORECASE),
                'severity': 'ERROR',
                'category': 'Filesystem Issue',
                'description': 'File permission issue',
                'auto_heal': False
            },
            
            # API Issues
            'api_error': {
                'pattern': re.compile(r'(HTTP.*5[0-9]{2}|internal server error|bad gateway|service unavailable)', re.IGNORECASE),
                'severity': 'ERROR',
                'category': 'API Issue',
                'description': 'API error detected',
                'auto_heal': True
            },
            
            # SSL/TLS Issues
            'ssl_certificate': {
                'pattern': re.compile(r'(certificate.*expired|ssl.*error|certificate.*invalid)', re.IGNORECASE),
                'severity': 'CRITICAL',
                'category': 'Security Issue',
                'description': 'SSL/TLS certificate issue',
                'auto_heal': False
            }
        }
    
    def add_log_file(self, file_path: str):
        """Add a log file to monitor"""
        path = Path(file_path)
        if path.exists():
            self.log_files.append(str(path))
            # Initialize file position to end of file
            self.file_positions[str(path)] = path.stat().st_size
            logger.info(f"Added log file for monitoring: {file_path}")
        else:
            logger.warning(f"Log file not found: {file_path}")
    
    def auto_discover_logs(self):
        """Automatically discover log files in common locations"""
        common_log_locations = [
            # Application logs
            './logs',
            './log',
            '../logs',
            './monitoring/server/logs',
            './model/logs',
            './incident-bot/logs',
            
            # System logs (Linux)
            '/var/log',
            '/var/log/syslog',
            '/var/log/messages',
            
            # Python logs
            './*.log',
            './**/*.log'
        ]
        
        for location in common_log_locations:
            try:
                location_path = Path(location)
                if location_path.is_file() and location_path.suffix == '.log':
                    self.add_log_file(str(location_path))
                elif location_path.is_dir():
                    for log_file in location_path.glob('*.log'):
                        self.add_log_file(str(log_file))
            except Exception as e:
                pass
    
    def analyze_log_line(self, line: str, source_file: str) -> List[Dict[str, Any]]:
        """
        Analyze a single log line for issues
        """
        issues = []
        
        for issue_name, pattern_info in self.issue_patterns.items():
            if pattern_info['pattern'].search(line):
                issue = {
                    'timestamp': datetime.now().isoformat(),
                    'issue_type': issue_name,
                    'severity': pattern_info['severity'],
                    'category': pattern_info['category'],
                    'description': pattern_info['description'],
                    'log_line': line.strip(),
                    'source_file': source_file,
                    'auto_heal': pattern_info['auto_heal'],
                    'resolved': False
                }
                issues.append(issue)
                self.issue_stats[issue_name] += 1
        
        return issues
    
    def monitor_file(self, file_path: str):
        """
        Monitor a single file for new log entries
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return
            
            current_size = path.stat().st_size
            last_position = self.file_positions.get(file_path, 0)
            
            # Check if file was rotated or truncated
            if current_size < last_position:
                last_position = 0
            
            # Read new content
            if current_size > last_position:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    for line in new_lines:
                        issues = self.analyze_log_line(line, file_path)
                        for issue in issues:
                            self.detected_issues.append(issue)
                            self.recent_issues.append(issue)
                            logger.warning(f"Issue detected: {issue['issue_type']} - {issue['description']}")
                    
                    self.file_positions[file_path] = f.tell()
        
        except Exception as e:
            logger.error(f"Error monitoring file {file_path}: {e}")
    
    def start_monitoring(self):
        """Start the log monitoring service"""
        if self.monitoring:
            logger.warning("Log monitoring already started")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Log monitoring started")
    
    def stop_monitoring(self):
        """Stop the log monitoring service"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Log monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Monitor all registered log files
                for log_file in self.log_files:
                    self.monitor_file(log_file)
                
                # Clean up old recent issues (older than 5 minutes)
                cutoff_time = datetime.now() - timedelta(minutes=5)
                self.recent_issues = [
                    issue for issue in self.recent_issues
                    if datetime.fromisoformat(issue['timestamp']) > cutoff_time
                ]
                
                # Sleep for 1 second before next check
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def get_recent_issues(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent issues"""
        return list(self.detected_issues)[-limit:]
    
    def get_issue_statistics(self) -> Dict[str, Any]:
        """Get statistics about detected issues"""
        total_issues = len(self.detected_issues)
        
        # Count by severity
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        
        for issue in self.detected_issues:
            severity_counts[issue['severity']] += 1
            category_counts[issue['category']] += 1
        
        return {
            'total_issues': total_issues,
            'recent_issues_5min': len(self.recent_issues),
            'severity_distribution': dict(severity_counts),
            'category_distribution': dict(category_counts),
            'issue_type_counts': dict(self.issue_stats),
            'monitoring_status': 'active' if self.monitoring else 'inactive',
            'monitored_files': len(self.log_files)
        }
    
    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """Get only critical and unresolved issues"""
        return [
            issue for issue in self.detected_issues
            if issue['severity'] in ['CRITICAL', 'ERROR'] and not issue['resolved']
        ]
    
    def mark_issue_resolved(self, issue_timestamp: str):
        """Mark an issue as resolved"""
        for issue in self.detected_issues:
            if issue['timestamp'] == issue_timestamp:
                issue['resolved'] = True
                logger.info(f"Issue marked as resolved: {issue['issue_type']}")
                break
    
    def get_system_health_score(self) -> float:
        """
        Calculate overall system health score based on recent issues
        Score from 0-100, where 100 is perfect health
        """
        if not self.recent_issues:
            return 100.0
        
        # Weight issues by severity
        severity_weights = {
            'CRITICAL': 10,
            'ERROR': 5,
            'WARNING': 2,
            'INFO': 0.5
        }
        
        total_weight = sum(
            severity_weights.get(issue['severity'], 1)
            for issue in self.recent_issues
        )
        
        # Calculate health score (max penalty is 100 points)
        health_score = max(0, 100 - total_weight)
        
        return round(health_score, 2)


# Global log monitor instance
log_monitor = LogMonitor()


def initialize_log_monitoring():
    """Initialize the log monitoring system"""
    # Auto-discover log files
    log_monitor.auto_discover_logs()
    
    # Add specific log files if they exist
    specific_logs = [
        './model/model.log',
        './monitoring/server/server.log',
        './incident-bot/incident.log',
        './monitoring/dashboard/dashboard.log'
    ]
    
    for log_file in specific_logs:
        log_monitor.add_log_file(log_file)
    
    # Start monitoring
    log_monitor.start_monitoring()
    
    logger.info(f"Log monitoring initialized with {len(log_monitor.log_files)} files")
    return log_monitor


if __name__ == "__main__":
    # Test the log monitor
    monitor = initialize_log_monitoring()
    
    try:
        while True:
            stats = monitor.get_issue_statistics()
            health = monitor.get_system_health_score()
            print(f"\n{'='*60}")
            print(f"System Health Score: {health}/100")
            print(f"Total Issues: {stats['total_issues']}")
            print(f"Recent Issues (5min): {stats['recent_issues_5min']}")
            print(f"Monitored Files: {stats['monitored_files']}")
            print(f"{'='*60}")
            time.sleep(10)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\nLog monitoring stopped")

