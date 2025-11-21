"""
Critical Services Monitor for Ubuntu
Monitors essential system services and their logs
"""

import subprocess
import json
import os
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
                'nginx': 'Web server - HTTP/HTTPS service',
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
        
        # File-based logging configuration
        self.log_file = '/var/log/critical_monitor.log'
        self.state_file = '/var/tmp/journalctl_cursor_critical.state'
        self.max_log_size = 10 * 1024 * 1024  # 10 MB
        self.last_cursor = None
        
        # Initialize log file
        self._init_log_file()
        
    def start_monitoring(self, interval_seconds: int = 30):
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
                # Write critical logs to file and maintain rotation
                self._write_critical_logs_to_file()
                self._maintain_log_file_size()
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
            # First try by unit name, if that fails try by identifier (SYSLOG_IDENTIFIER)
            result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', str(lines), '--output=json', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # If no results by unit, try by SYSLOG_IDENTIFIER (what logger uses)
            # Also filter for CRITICAL priority (0-2) to catch test errors
            if result.returncode != 0 or not result.stdout.strip():
                logger.debug(f"No logs found for unit {service_name}, trying by identifier")
                result = subprocess.run(
                    ['journalctl', 'SYSLOG_IDENTIFIER=' + service_name, '-n', str(lines), '--output=json', '--no-pager', '-p', '0..2', '--since', '5 minutes ago'],
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
            # Priority levels: 0=EMERG, 1=ALERT, 2=CRIT, 3=ERR, 4=WARNING, 5=NOTICE, 6=INFO, 7=DEBUG
            # For CRITICAL detection: priority <= 2 should be CRITICAL
            if priority <= 2:
                level = 'CRITICAL'  # EMERG/ALERT/CRIT -> CRITICAL
            elif priority <= 3:
                level = 'ERROR'     # ERR -> ERROR
            elif priority <= 4:
                level = 'WARNING'   # WARNING -> WARNING
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
        
        # Also collect any CRITICAL priority logs (priority <= 2) from system journal
        # This catches logs written with logger -p 2 or systemd-cat -p crit
        try:
            # Collect CRITICAL logs (priority 0-2) from the last 2 minutes
            result = subprocess.run(
                ['journalctl', '-p', '2', '-n', '100', '--output=json', '--no-pager', '--since', '2 minutes ago'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                all_monitored_services = []
                for cat, services in self.critical_services.items():
                    all_monitored_services.extend(services.keys())
                
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            priority = int(entry.get('PRIORITY', 6))
                            
                            # Only process CRITICAL priority logs (0-2)
                            if priority > 2:
                                continue
                            
                            # Extract service name from SYSLOG_IDENTIFIER or _SYSTEMD_UNIT
                            syslog_id = entry.get('SYSLOG_IDENTIFIER', '')
                            systemd_unit = entry.get('_SYSTEMD_UNIT', '')
                            message = (entry.get('MESSAGE', '') or '').lower()
                            service_name = syslog_id or systemd_unit.replace('.service', '').replace('@', '-at-')
                            
                            matched_service = None
                            matched_category = None
                            
                            # PRIORITY 1: Check SYSLOG_IDENTIFIER directly - if it matches a monitored service, use it
                            # This catches logs created with "logger -t nginx -p 2"
                            if syslog_id and syslog_id in all_monitored_services:
                                matched_service = syslog_id
                                for cat, services in self.critical_services.items():
                                    if syslog_id in services:
                                        matched_category = cat
                                        break
                            
                            # PRIORITY 2: Check message content for service names (highest priority for test logs)
                            # This catches logs where service name is in the message
                            if not matched_service:
                                for cat, services in self.critical_services.items():
                                    for monitored_svc in services.keys():
                                        if monitored_svc.lower() in message:
                                            matched_service = monitored_svc
                                            matched_category = cat
                                            logger.debug(f"Matched service '{monitored_svc}' from message content")
                                            break
                                    if matched_service:
                                        break
                            
                            # PRIORITY 3: Check if service_name (from syslog_id or unit) matches a monitored service
                            if not matched_service and service_name in all_monitored_services:
                                matched_service = service_name
                                for cat, services in self.critical_services.items():
                                    if service_name in services:
                                        matched_category = cat
                                        break
                            
                            # PRIORITY 4: Try to match by partial name in identifiers
                            if not matched_service:
                                service_lower = service_name.lower()
                                syslog_lower = syslog_id.lower() if syslog_id else ''
                                unit_lower = systemd_unit.lower() if systemd_unit else ''
                                
                                for cat, services in self.critical_services.items():
                                    for monitored_svc in services.keys():
                                        svc_lower = monitored_svc.lower()
                                        if (svc_lower in service_lower or svc_lower in syslog_lower or 
                                            svc_lower in unit_lower or monitored_svc in service_name):
                                            matched_service = monitored_svc
                                            matched_category = cat
                                            break
                                    if matched_service:
                                        break
                            
                            # PRIORITY 5: Check for common service names in message or identifiers
                            if not matched_service:
                                if ('nginx' in message or 'nginx' in syslog_lower or 
                                    'nginx' in service_lower or 'nginx' in unit_lower):
                                    matched_service = 'nginx'
                                    matched_category = 'CRITICAL'
                                elif ('docker' in message or 'docker' in syslog_lower or 
                                      'docker' in service_lower or 'docker' in unit_lower):
                                    matched_service = 'docker'
                                    matched_category = 'CRITICAL'
                                elif ('apache' in message or 'httpd' in message or 
                                      'apache' in syslog_lower or 'httpd' in syslog_lower):
                                    matched_service = 'apache'
                                    matched_category = 'IMPORTANT'
                                elif ('mysql' in message or 'mariadb' in message or 
                                      'mysql' in syslog_lower or 'mariadb' in syslog_lower):
                                    matched_service = 'mysql'
                                    matched_category = 'IMPORTANT'
                                elif ('postgres' in message or 'postgres' in syslog_lower):
                                    matched_service = 'postgresql'
                                    matched_category = 'IMPORTANT'
                            
                            # PRIORITY 6: Fallback - skip "sudo" logs unless they mention a service
                            # Many sudo password prompts create CRITICAL logs that aren't actual service errors
                            if not matched_service:
                                # If syslog_id is sudo but message mentions a service, use the service
                                if syslog_id and syslog_id.lower() == 'sudo':
                                    for cat, services in self.critical_services.items():
                                        for monitored_svc in services.keys():
                                            if monitored_svc.lower() in message:
                                                matched_service = monitored_svc
                                                matched_category = cat
                                                logger.debug(f"Matched service '{monitored_svc}' from sudo log message")
                                                break
                                        if matched_service:
                                            break
                                    
                                    # If no service found in sudo log message, skip it (likely password prompt)
                                    if not matched_service:
                                        continue
                                elif syslog_id and syslog_id.lower() not in ['sudo', 'systemd', 'user']:
                                    # Use syslog_id only if it's not a common system component
                                    matched_service = syslog_id
                                    matched_category = 'CRITICAL'
                                elif systemd_unit:
                                    matched_service = systemd_unit.replace('.service', '').replace('@', '-at-')
                                    matched_category = 'CRITICAL'
                                else:
                                    # Skip system logs without clear service attribution
                                    continue
                            
                            if matched_service:
                                parsed = self._parse_journal_entry(entry, matched_service, matched_category)
                                if parsed:
                                    # Include all CRITICAL priority logs (level will be CRITICAL for priority <= 2)
                                    # Also include ERROR and WARNING from CRITICAL category services
                                    level = parsed.get('level', '').upper()
                                    if level == 'CRITICAL' or (level in ['ERROR', 'WARNING'] and matched_category == 'CRITICAL'):
                                        new_logs.append(parsed)
                                        logger.info(f"Added CRITICAL log: service={matched_service}, level={level}, priority={priority}, syslog_id={syslog_id}, unit={systemd_unit}")
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.debug(f"Error parsing CRITICAL log entry: {e}")
                            continue
        except Exception as e:
            logger.debug(f"Error collecting CRITICAL priority logs: {e}")
        
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
        """Get critical issues (errors from CRITICAL/IMPORTANT category services)"""
        issues = []
        
        # Keywords that indicate problems even if level is INFO
        problem_keywords = ['error', 'fail', 'failed', 'exception', 'critical', 'warning', 
                           'timeout', 'crash', 'abort', 'denied', 'refused', 'unavailable',
                           'not found', 'cannot', 'unable', 'broken', 'invalid', 'degraded']
        
        total_logs = len(self.service_logs)
        
        # Limit processing to avoid timeout - only check last 200 logs max (most recent)
        logs_to_check = self.service_logs[-200:] if total_logs > 200 else self.service_logs
        
        # Don't log every time to avoid spam
        if total_logs > 200:
            logger.debug(f"Checking last 200 of {total_logs} total logs for critical issues")
        
        for log in logs_to_check:
            level = log.get('level', '').upper()
            category = log.get('category', '')
            message = (log.get('message', '') or '').lower()
            priority = log.get('priority', 6)
            
            # Include ERROR and WARNING from CRITICAL and IMPORTANT categories
            is_error_or_warning = level in ['ERROR', 'WARNING', 'ERR', 'WARN', 'CRITICAL', 'CRIT']
            is_critical_or_important = category in ['CRITICAL', 'IMPORTANT']
            
            # Also include logs with problem keywords from CRITICAL or IMPORTANT category
            has_problem_keyword = is_critical_or_important and any(keyword in message for keyword in problem_keywords)
            
            # Include if it matches our criteria
            if (is_critical_or_important and is_error_or_warning) or has_problem_keyword:
                # Create issue entry with severity field for frontend compatibility
                issue = log.copy()
                
                # Determine severity based on priority (most reliable)
                # Priority 0-2 = CRITICAL, Priority 3 = ERROR, Priority 4 = WARNING
                if priority <= 2:
                    issue['severity'] = 'CRITICAL'  # Priority 0,1,2 = CRITICAL
                elif priority == 3:
                    issue['severity'] = 'ERROR'  # Priority 3 = ERROR
                elif priority == 4:
                    issue['severity'] = 'WARNING'  # Priority 4 = WARNING
                elif level in ['CRITICAL', 'CRIT']:
                    issue['severity'] = 'CRITICAL'  # Fallback: if level says CRITICAL
                elif level in ['ERROR', 'ERR']:
                    issue['severity'] = 'ERROR'
                elif level in ['WARNING', 'WARN']:
                    issue['severity'] = 'WARNING'
                elif has_problem_keyword:
                    issue['severity'] = 'WARNING'
                else:
                    issue['severity'] = level or 'UNKNOWN'
                
                issues.append(issue)
        
        logger.debug(f"Found {len(issues)} critical issues from {total_logs} total logs")
        
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
    
    def _init_log_file(self):
        """Initialize the critical log file with proper permissions"""
        try:
            # Ensure log file exists
            if not os.path.exists(self.log_file):
                # Try to create with write permission
                try:
                    with open(self.log_file, 'w') as f:
                        f.write(f"[{datetime.now().isoformat()}] Critical Monitor Log File Initialized\n")
                    os.chmod(self.log_file, 0o640)
                    logger.info(f"Created critical log file: {self.log_file}")
                except PermissionError:
                    # Fall back to user-writable location if no sudo
                    self.log_file = os.path.expanduser('~/critical_monitor.log')
                    with open(self.log_file, 'w') as f:
                        f.write(f"[{datetime.now().isoformat()}] Critical Monitor Log File Initialized\n")
                    logger.info(f"Created critical log file in home directory: {self.log_file}")
            else:
                # Ensure write permission
                try:
                    os.chmod(self.log_file, 0o640)
                except PermissionError:
                    pass
                    
            # Load last cursor if exists
            if os.path.exists(self.state_file):
                try:
                    with open(self.state_file, 'r') as f:
                        self.last_cursor = f.read().strip()
                except Exception as e:
                    logger.debug(f"Could not load cursor: {e}")
        except Exception as e:
            logger.warning(f"Could not initialize log file: {e}")
    
    def _write_critical_logs_to_file(self):
        """Write new critical logs (priority 0-3) to the log file using cursor tracking"""
        try:
            hostname = os.uname().nodename
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get new critical logs since last cursor (priority 0-3: EMERG, ALERT, CRIT, ERR)
            cmd = ['journalctl', '-p', '3', '--output=json', '--no-pager']
            
            if self.last_cursor:
                # Get logs after the cursor
                result = subprocess.run(
                    cmd + ['--after-cursor', self.last_cursor],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                # First run: get last 50 messages
                result = subprocess.run(
                    cmd + ['-n', '50'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            # Update cursor
            cursor_result = subprocess.run(
                ['journalctl', '-p', '3', '-n', '1', '--show-cursor', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if cursor_result.returncode == 0 and 'cursor:' in cursor_result.stdout:
                self.last_cursor = cursor_result.stdout.split('cursor: ')[1].strip()
                # Save cursor to state file
                try:
                    with open(self.state_file, 'w') as f:
                        f.write(self.last_cursor)
                except Exception as e:
                    logger.debug(f"Could not save cursor: {e}")
            
            # Parse and write new logs, also add to service_logs for dashboard
            if result.returncode == 0 and result.stdout.strip():
                new_logs = []
                parsed_logs_for_dashboard = []
                
                # Get all monitored services for matching
                all_monitored_services = []
                for cat, services in self.critical_services.items():
                    all_monitored_services.extend(services.keys())
                
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            priority = int(entry.get('PRIORITY', 6))
                            
                            # Only process critical logs (priority 0-3)
                            if priority > 3:
                                continue
                            
                            # Format log entry for file
                            timestamp_us = int(entry.get('__REALTIME_TIMESTAMP', 0))
                            log_time = datetime.fromtimestamp(timestamp_us / 1000000)
                            message = entry.get('MESSAGE', '')
                            syslog_id = entry.get('SYSLOG_IDENTIFIER', 'unknown')
                            unit = entry.get('_SYSTEMD_UNIT', '')
                            service = syslog_id or unit.replace('.service', '') or 'system'
                            
                            # Format priority level
                            priority_levels = {0: 'EMERG', 1: 'ALERT', 2: 'CRIT', 3: 'ERR'}
                            level = priority_levels.get(priority, f'PRIORITY-{priority}')
                            
                            log_line = f"{log_time.strftime('%b %d %H:%M:%S')} {hostname} {service}[{syslog_id}]: {level}: {message}"
                            new_logs.append(log_line)
                            
                            # Also parse for dashboard (same logic as collect_all_service_logs)
                            service_name = syslog_id or unit.replace('.service', '').replace('@', '-at-')
                            message_lower = message.lower()
                            
                            # Match service to monitored services (same priority logic as collect_all_service_logs)
                            matched_service = None
                            matched_category = None
                            
                            # PRIORITY 1: Check SYSLOG_IDENTIFIER directly
                            if syslog_id and syslog_id in all_monitored_services:
                                matched_service = syslog_id
                                for cat, services in self.critical_services.items():
                                    if syslog_id in services:
                                        matched_category = cat
                                        break
                            
                            # PRIORITY 2: Check message content for service names
                            if not matched_service:
                                for cat, services in self.critical_services.items():
                                    for monitored_svc in services.keys():
                                        if monitored_svc.lower() in message_lower:
                                            matched_service = monitored_svc
                                            matched_category = cat
                                            break
                                    if matched_service:
                                        break
                            
                            # PRIORITY 3: Check if service_name matches
                            if not matched_service and service_name in all_monitored_services:
                                matched_service = service_name
                                for cat, services in self.critical_services.items():
                                    if service_name in services:
                                        matched_category = cat
                                        break
                            
                            # PRIORITY 4: Try to match by partial name
                            if not matched_service:
                                service_lower = service_name.lower()
                                syslog_lower = syslog_id.lower() if syslog_id else ''
                                unit_lower = unit.lower() if unit else ''
                                
                                for cat, services in self.critical_services.items():
                                    for monitored_svc in services.keys():
                                        svc_lower = monitored_svc.lower()
                                        if (svc_lower in service_lower or svc_lower in syslog_lower or 
                                            svc_lower in unit_lower or monitored_svc in service_name):
                                            matched_service = monitored_svc
                                            matched_category = cat
                                            break
                                    if matched_service:
                                        break
                            
                            # PRIORITY 5: Check for common service names
                            if not matched_service:
                                if ('nginx' in message_lower or 'nginx' in syslog_lower or 
                                    'nginx' in service_lower or 'nginx' in unit_lower):
                                    matched_service = 'nginx'
                                    matched_category = 'CRITICAL'
                                elif ('docker' in message_lower or 'docker' in syslog_lower or 
                                      'docker' in service_lower or 'docker' in unit_lower):
                                    matched_service = 'docker'
                                    matched_category = 'CRITICAL'
                                elif ('apache' in message_lower or 'httpd' in message_lower or 
                                      'apache' in syslog_lower or 'httpd' in syslog_lower):
                                    matched_service = 'apache'
                                    matched_category = 'IMPORTANT'
                                elif ('mysql' in message_lower or 'mariadb' in message_lower or 
                                      'mysql' in syslog_lower or 'mariadb' in syslog_lower):
                                    matched_service = 'mysql'
                                    matched_category = 'IMPORTANT'
                                elif ('postgres' in message_lower or 'postgres' in syslog_lower):
                                    matched_service = 'postgresql'
                                    matched_category = 'IMPORTANT'
                            
                            # PRIORITY 6: Fallback - skip "sudo" logs unless they mention a service
                            if not matched_service:
                                if syslog_id and syslog_id.lower() == 'sudo':
                                    for cat, services in self.critical_services.items():
                                        for monitored_svc in services.keys():
                                            if monitored_svc.lower() in message_lower:
                                                matched_service = monitored_svc
                                                matched_category = cat
                                                break
                                        if matched_service:
                                            break
                                    if not matched_service:
                                        continue  # Skip sudo logs without service mention
                                elif syslog_id and syslog_id.lower() not in ['sudo', 'systemd', 'user']:
                                    matched_service = syslog_id
                                    matched_category = 'CRITICAL'
                                elif unit:
                                    matched_service = unit.replace('.service', '').replace('@', '-at-')
                                    matched_category = 'CRITICAL'
                                else:
                                    continue  # Skip logs without clear service attribution
                            
                            # Parse entry for dashboard
                            parsed = self._parse_journal_entry(entry, matched_service, matched_category)
                            if parsed:
                                parsed_logs_for_dashboard.append(parsed)
                                
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.debug(f"Error parsing journal entry for file: {e}")
                            continue
                
                # Write new logs to file
                if new_logs:
                    try:
                        with open(self.log_file, 'a') as f:
                            f.write(f"\n[{timestamp}] --- New Critical Errors on {hostname} ---\n")
                            for log_line in new_logs:
                                f.write(log_line + '\n')
                            f.write("----------------------------------------------\n")
                        logger.debug(f"Wrote {len(new_logs)} critical logs to {self.log_file}")
                    except PermissionError:
                        logger.debug(f"Permission denied writing to {self.log_file}")
                    except Exception as e:
                        logger.debug(f"Error writing to log file: {e}")
                
                # Also add parsed logs to service_logs for dashboard
                if parsed_logs_for_dashboard:
                    for parsed_log in parsed_logs_for_dashboard:
                        # Check if log already exists (avoid duplicates)
                        is_duplicate = any(
                            log.get('timestamp') == parsed_log.get('timestamp') and
                            log.get('service') == parsed_log.get('service') and
                            log.get('message') == parsed_log.get('message')
                            for log in self.service_logs
                        )
                        
                        if not is_duplicate:
                            self.service_logs.append(parsed_log)
                            logger.debug(f"Added log to service_logs from file logging: service={parsed_log.get('service')}, level={parsed_log.get('level')}")
                    
                    # Maintain size limit
                    if len(self.service_logs) > self.max_logs:
                        excess = len(self.service_logs) - self.max_logs
                        self.service_logs = self.service_logs[excess:]
        except Exception as e:
            logger.debug(f"Error writing critical logs to file: {e}")
    
    def _maintain_log_file_size(self):
        """Maintain log file size by truncating when it exceeds max size"""
        try:
            if not os.path.exists(self.log_file):
                return
            
            # Get current file size
            file_size = os.path.getsize(self.log_file)
            
            if file_size > self.max_log_size:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Log file exceeded {self.max_log_size / 1024 / 1024:.1f}MB, truncating...")
                
                # Read the last half of the file (keep most recent logs)
                try:
                    with open(self.log_file, 'rb') as f:
                        f.seek(-(self.max_log_size // 2), os.SEEK_END)
                        # Skip partial line
                        f.readline()
                        remaining = f.read()
                    
                    # Write truncated content
                    with open(self.log_file, 'wb') as f:
                        f.write(f"[{timestamp}] --- Log exceeded {self.max_log_size / 1024 / 1024:.1f}MB, truncated to keep last {self.max_log_size // 2 / 1024 / 1024:.1f}MB ---\n".encode())
                        f.write(remaining)
                    
                    new_size = os.path.getsize(self.log_file)
                    logger.info(f"Log file truncated: {new_size / 1024 / 1024:.2f}MB")
                except Exception as e:
                    logger.error(f"Error truncating log file: {e}")
        except Exception as e:
            logger.debug(f"Error maintaining log file size: {e}")
    
    def get_log_file_path(self) -> str:
        """Get the path to the critical log file"""
        return self.log_file


# Singleton instance
_critical_monitor_instance = None

def initialize_critical_services_monitor():
    """Initialize the critical services monitor"""
    global _critical_monitor_instance
    
    if _critical_monitor_instance is None:
        _critical_monitor_instance = CriticalServicesMonitor()
        _critical_monitor_instance.start_monitoring(interval_seconds=10)
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

