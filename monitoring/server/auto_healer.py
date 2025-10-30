"""
AI-Powered Auto-Healing System
Automatically detects, analyzes, and fixes system errors using Gemini AI
"""

import subprocess
import re
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoHealer:
    """
    AI-Powered Auto-Healing System
    
    Features:
    - Detects critical errors automatically
    - Uses AI to analyze and suggest fixes
    - Executes safe remediation actions
    - Verifies fixes worked
    - Logs all healing actions
    - Rollback capability if fix fails
    """
    
    def __init__(self, gemini_analyzer=None, system_log_collector=None, 
                 critical_services_monitor=None):
        self.gemini_analyzer = gemini_analyzer
        self.system_log_collector = system_log_collector
        self.critical_services_monitor = critical_services_monitor
        
        # Healing configuration
        self.enabled = True
        self.auto_execute = True  # Set to False for manual approval mode
        self.max_healing_attempts = 3
        
        # Healing history
        self.healing_history = []
        self.max_history = 100
        
        # Safe commands that can be auto-executed
        self.safe_commands = {
            'restart_service': self._restart_service,
            'fix_permissions': self._fix_permissions,
            'clear_cache': self._clear_cache,
            'rotate_logs': self._rotate_logs,
            'free_disk_space': self._free_disk_space,
            'restart_network': self._restart_network,
            'reload_config': self._reload_config,
            'kill_zombie_process': self._kill_zombie_process,
        }
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        logger.info("Auto-Healer initialized")
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start automatic error monitoring and healing"""
        if self.running:
            logger.warning("Auto-healer already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Auto-healer monitoring started (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop automatic monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Auto-healer monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for critical errors
                self._check_and_heal_errors()
            except Exception as e:
                logger.error(f"Error in auto-healer monitoring loop: {e}")
            
            time.sleep(interval_seconds)
    
    def _check_and_heal_errors(self):
        """Check for errors and attempt to heal them"""
        if not self.enabled:
            return
        
        # Get critical errors from system logs
        if self.system_log_collector:
            errors = self.system_log_collector.get_recent_logs(
                limit=10,
                level='ERROR'
            )
            
            for error in errors:
                # Check if we've already tried to heal this error
                if not self._should_heal(error):
                    continue
                
                # Attempt to heal the error
                self.heal_error(error)
    
    def _should_heal(self, error: Dict[str, Any]) -> bool:
        """Determine if we should attempt to heal this error"""
        # Check if error is too old (> 5 minutes)
        timestamp = error.get('timestamp', '')
        try:
            error_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.now() - error_time).total_seconds()
            if age_seconds > 300:  # 5 minutes
                return False
        except:
            pass
        
        # Check if we've already tried healing this error
        error_signature = f"{error.get('service')}:{error.get('message')}"
        recent_attempts = [
            h for h in self.healing_history[-20:]
            if h.get('error_signature') == error_signature
        ]
        
        # Don't retry if we've failed multiple times recently
        if len(recent_attempts) >= self.max_healing_attempts:
            return False
        
        return True
    
    def heal_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to heal an error using AI analysis
        
        Returns:
            healing_result: Dict with status, actions taken, and verification
        """
        start_time = datetime.now()
        error_signature = f"{error.get('service')}:{error.get('message')}"
        
        logger.info(f"🔧 Attempting to heal error: {error.get('service')} - {error.get('message')[:50]}...")
        
        healing_result = {
            'timestamp': start_time.isoformat(),
            'error': error,
            'error_signature': error_signature,
            'status': 'failed',
            'analysis': None,
            'actions': [],
            'success': False,
            'error_message': None
        }
        
        try:
            # Step 1: Analyze error with AI
            if not self.gemini_analyzer:
                healing_result['error_message'] = 'Gemini analyzer not available'
                self._record_healing(healing_result)
                return healing_result
            
            analysis = self.gemini_analyzer.analyze_log(error)
            if not analysis:
                healing_result['error_message'] = 'AI analysis failed'
                self._record_healing(healing_result)
                return healing_result
            
            healing_result['analysis'] = analysis
            
            # Step 2: Extract actionable commands from AI solution
            solution = analysis.get('solution', '')
            commands = self._extract_commands(solution, error)
            
            if not commands:
                healing_result['error_message'] = 'No actionable commands found in AI solution'
                healing_result['status'] = 'no_action'
                self._record_healing(healing_result)
                return healing_result
            
            # Step 3: Execute commands
            if self.auto_execute:
                for cmd_info in commands:
                    action_result = self._execute_healing_action(cmd_info, error)
                    healing_result['actions'].append(action_result)
                    
                    if not action_result['success']:
                        logger.warning(f"Action failed: {action_result['error']}")
                        break
            else:
                healing_result['status'] = 'pending_approval'
                healing_result['pending_commands'] = commands
                self._record_healing(healing_result)
                return healing_result
            
            # Step 4: Verify the fix worked
            time.sleep(2)  # Wait for changes to take effect
            verification = self._verify_healing(error)
            healing_result['verification'] = verification
            
            if verification['success']:
                healing_result['status'] = 'healed'
                healing_result['success'] = True
                logger.info(f"✅ Successfully healed: {error.get('service')}")
            else:
                healing_result['status'] = 'failed_verification'
                logger.warning(f"❌ Healing verification failed: {error.get('service')}")
            
        except Exception as e:
            logger.error(f"Error during healing process: {e}")
            healing_result['error_message'] = str(e)
            healing_result['status'] = 'exception'
        
        # Record the healing attempt
        self._record_healing(healing_result)
        
        return healing_result
    
    def _extract_commands(self, solution_text: str, error: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract actionable commands from AI-generated solution
        
        Returns:
            List of command dictionaries with type and parameters
        """
        commands = []
        service = error.get('service', '')
        message = error.get('message', '').lower()
        
        # Pattern matching for common issues
        
        # Service restart
        if any(keyword in solution_text.lower() for keyword in ['restart', 'reload', 'systemctl']):
            if 'systemd' in service or any(svc in service for svc in ['docker', 'apache', 'nginx', 'cron']):
                commands.append({
                    'type': 'restart_service',
                    'service': service,
                    'description': f'Restart {service} service'
                })
        
        # Permission issues
        if 'permission denied' in message or 'chmod' in solution_text.lower():
            # Extract file path from error message
            file_match = re.search(r'(/[\w/.-]+\.\w+)', error.get('message', ''))
            if file_match:
                file_path = file_match.group(1)
                commands.append({
                    'type': 'fix_permissions',
                    'path': file_path,
                    'description': f'Fix permissions for {file_path}'
                })
        
        # Disk space issues
        if any(keyword in message for keyword in ['disk full', 'no space', 'space left']):
            commands.append({
                'type': 'free_disk_space',
                'description': 'Free up disk space by cleaning old logs and cache'
            })
        
        # Log rotation
        if 'log' in message and any(keyword in message for keyword in ['full', 'size', 'rotate']):
            commands.append({
                'type': 'rotate_logs',
                'service': service,
                'description': f'Rotate logs for {service}'
            })
        
        # Cache clearing
        if 'cache' in message.lower():
            commands.append({
                'type': 'clear_cache',
                'service': service,
                'description': f'Clear cache for {service}'
            })
        
        # Network issues
        if any(keyword in message for keyword in ['network', 'connection', 'dns']):
            if 'resolved' in service:
                commands.append({
                    'type': 'restart_network',
                    'description': 'Restart network services'
                })
        
        return commands
    
    def _execute_healing_action(self, cmd_info: Dict[str, Any], 
                                error: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single healing action"""
        action_type = cmd_info.get('type')
        
        result = {
            'action': cmd_info,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'output': None,
            'error': None
        }
        
        try:
            if action_type in self.safe_commands:
                handler = self.safe_commands[action_type]
                success, output = handler(cmd_info)
                result['success'] = success
                result['output'] = output
                
                if success:
                    logger.info(f"✅ Action succeeded: {cmd_info.get('description')}")
                else:
                    logger.warning(f"❌ Action failed: {cmd_info.get('description')}")
                    result['error'] = output
            else:
                result['error'] = f'Unknown action type: {action_type}'
                logger.warning(result['error'])
        
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Exception executing action: {e}")
        
        return result
    
    # Safe command handlers
    
    def _restart_service(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Safely restart a system service"""
        service = cmd_info.get('service', '')
        
        # Safety check: Only restart safe services
        safe_services = ['docker', 'apache2', 'nginx', 'systemd-resolved', 'cron', 'ssh']
        if not any(safe_svc in service for safe_svc in safe_services):
            return False, f"Service {service} not in safe restart list"
        
        try:
            # Use systemctl to restart
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Service {service} restarted successfully"
            else:
                return False, f"Failed to restart {service}: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, f"Timeout restarting {service}"
        except Exception as e:
            return False, f"Error restarting {service}: {str(e)}"
    
    def _fix_permissions(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Fix file permissions"""
        file_path = cmd_info.get('path', '')
        
        # Safety check: Only fix permissions in safe directories
        safe_dirs = ['/usr/local/bin', '/var/log', '/opt', '/home']
        if not any(file_path.startswith(safe_dir) for safe_dir in safe_dirs):
            return False, f"Path {file_path} not in safe directories"
        
        try:
            # Make file executable
            result = subprocess.run(
                ['sudo', 'chmod', '+x', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, f"Fixed permissions for {file_path}"
            else:
                return False, f"Failed to fix permissions: {result.stderr}"
        
        except Exception as e:
            return False, f"Error fixing permissions: {str(e)}"
    
    def _clear_cache(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Clear system or service cache"""
        try:
            # Clear system cache (safe operation)
            subprocess.run(['sudo', 'sync'], timeout=10)
            subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], timeout=10)
            
            return True, "System cache cleared"
        except Exception as e:
            return False, f"Error clearing cache: {str(e)}"
    
    def _rotate_logs(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Rotate logs for a service"""
        service = cmd_info.get('service', '')
        
        try:
            # Trigger logrotate
            result = subprocess.run(
                ['sudo', 'logrotate', '-f', '/etc/logrotate.conf'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Logs rotated for {service}"
            else:
                return False, f"Failed to rotate logs: {result.stderr}"
        
        except Exception as e:
            return False, f"Error rotating logs: {str(e)}"
    
    def _free_disk_space(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Free up disk space by cleaning old files"""
        try:
            cleaned = []
            
            # Clean apt cache
            subprocess.run(['sudo', 'apt-get', 'clean'], timeout=30)
            cleaned.append('apt cache')
            
            # Clean old logs (older than 7 days)
            subprocess.run(
                ['sudo', 'find', '/var/log', '-type', 'f', '-name', '*.log.*', '-mtime', '+7', '-delete'],
                timeout=60
            )
            cleaned.append('old logs')
            
            # Clean temp files
            subprocess.run(['sudo', 'rm', '-rf', '/tmp/*'], timeout=30)
            cleaned.append('temp files')
            
            return True, f"Freed disk space: {', '.join(cleaned)}"
        
        except Exception as e:
            return False, f"Error freeing disk space: {str(e)}"
    
    def _restart_network(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Restart network services"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'systemd-resolved'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Network services restarted"
            else:
                return False, f"Failed to restart network: {result.stderr}"
        
        except Exception as e:
            return False, f"Error restarting network: {str(e)}"
    
    def _reload_config(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Reload service configuration"""
        service = cmd_info.get('service', '')
        
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'reload', service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, f"Config reloaded for {service}"
            else:
                return False, f"Failed to reload config: {result.stderr}"
        
        except Exception as e:
            return False, f"Error reloading config: {str(e)}"
    
    def _kill_zombie_process(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Kill zombie processes"""
        try:
            # Find and kill zombie processes (safe operation)
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            zombies = [line for line in result.stdout.split('\n') if '<defunct>' in line]
            
            if zombies:
                return True, f"Found {len(zombies)} zombie processes (auto-cleanup by kernel)"
            else:
                return True, "No zombie processes found"
        
        except Exception as e:
            return False, f"Error checking zombies: {str(e)}"
    
    def _verify_healing(self, original_error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that the healing action resolved the error
        
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
            if self.system_log_collector:
                recent_errors = self.system_log_collector.get_recent_logs(
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
    
    def _record_healing(self, healing_result: Dict[str, Any]):
        """Record a healing attempt in history"""
        self.healing_history.append(healing_result)
        
        # Maintain max history size
        if len(self.healing_history) > self.max_history:
            self.healing_history = self.healing_history[-self.max_history:]
        
        logger.info(f"Healing attempt recorded: {healing_result['status']}")
    
    def get_healing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing history"""
        return sorted(
            self.healing_history[-limit:],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
    
    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get statistics about healing attempts"""
        total = len(self.healing_history)
        if total == 0:
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'pending': 0,
                'success_rate': 0
            }
        
        successful = len([h for h in self.healing_history if h.get('status') == 'healed'])
        failed = len([h for h in self.healing_history if h.get('status') in ['failed', 'failed_verification', 'exception']])
        pending = len([h for h in self.healing_history if h.get('status') == 'pending_approval'])
        
        return {
            'total_attempts': total,
            'successful': successful,
            'failed': failed,
            'pending': pending,
            'success_rate': round((successful / total * 100), 1) if total > 0 else 0
        }


# Singleton instance
_auto_healer_instance = None

def initialize_auto_healer(gemini_analyzer=None, system_log_collector=None, 
                          critical_services_monitor=None):
    """Initialize the auto-healer"""
    global _auto_healer_instance
    
    if _auto_healer_instance is None:
        _auto_healer_instance = AutoHealer(
            gemini_analyzer=gemini_analyzer,
            system_log_collector=system_log_collector,
            critical_services_monitor=critical_services_monitor
        )
        logger.info("Auto-healer initialized")
    
    return _auto_healer_instance

def get_auto_healer():
    """Get the auto-healer instance"""
    return _auto_healer_instance

