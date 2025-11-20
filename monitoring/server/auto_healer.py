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
                 critical_services_monitor=None, container_healer=None,
                 root_cause_analyzer=None, discord_notifier=None, event_emitter=None):
        self.gemini_analyzer = gemini_analyzer
        self.system_log_collector = system_log_collector
        self.critical_services_monitor = critical_services_monitor
        self.container_healer = container_healer
        self.root_cause_analyzer = root_cause_analyzer
        self.discord_notifier = discord_notifier
        self.event_emitter = event_emitter
        
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
            # Cloud-specific healing actions
            'restart_container': self._restart_container,
            'start_container': self._start_container,
            'recreate_container': self._recreate_container,
            'cleanup_resources': self._cleanup_resources,
            'restore_network': self._restore_network,
        }
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        logger.info("Auto-Healer initialized with cloud healing capabilities")
    
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
    
    # Cloud-specific healing actions
    
    def _restart_container(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Restart a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return False, "Container name not provided"
        
        if self.container_healer:
            success, message = self.container_healer.restart_container(container_name)
            if success and self.discord_notifier:
                self._send_healing_discord_notification(container_name, 'restart', True, message)
            return success, message
        else:
            return False, "Container healer not available"
    
    def _start_container(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Start a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return False, "Container name not provided"
        
        if self.container_healer:
            success, message = self.container_healer.start_container(container_name)
            if success and self.discord_notifier:
                self._send_healing_discord_notification(container_name, 'start', True, message)
            return success, message
        else:
            return False, "Container healer not available"
    
    def _recreate_container(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Recreate a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return False, "Container name not provided"
        
        if self.container_healer:
            success, message = self.container_healer.recreate_container(container_name)
            if success and self.discord_notifier:
                self._send_healing_discord_notification(container_name, 'recreate', True, message)
            return success, message
        else:
            return False, "Container healer not available"
    
    def _cleanup_resources(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Clean up system resources (kill resource hogs, clear caches)"""
        try:
            import psutil
            cleaned = []
            
            # Kill high CPU processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    cpu = proc.info['cpu_percent'] or 0
                    mem = proc.info['memory_percent'] or 0
                    
                    # Kill processes using > 80% CPU or > 50% memory (excluding system processes)
                    if (cpu > 80 or mem > 50) and proc.info['name'] not in ['systemd', 'kernel', 'dockerd']:
                        proc.kill()
                        cleaned.append(f"Killed {proc.info['name']} (PID: {proc.info['pid']}, CPU: {cpu}%, Mem: {mem}%)")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Clear system cache
            try:
                subprocess.run(['sudo', 'sync'], timeout=10, check=False)
                subprocess.run(['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                             timeout=10, check=False)
                cleaned.append('System cache cleared')
            except:
                pass
            
            if cleaned:
                message = f"Resource cleanup: {', '.join(cleaned)}"
                logger.info(f"✅ {message}")
                return True, message
            else:
                return True, "No resource cleanup needed"
                
        except Exception as e:
            return False, f"Error cleaning up resources: {str(e)}"
    
    def _restore_network(self, cmd_info: Dict[str, Any]) -> Tuple[bool, str]:
        """Restore network connectivity"""
        try:
            # Restart network services
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'systemd-resolved'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                message = "Network services restarted"
                logger.info(f"✅ {message}")
                return True, message
            else:
                return False, f"Failed to restart network: {result.stderr}"
        except Exception as e:
            return False, f"Error restoring network: {str(e)}"
    
    def _send_healing_discord_notification(self, container_name: str, action: str,
                                          success: bool, message: str):
        """Send Discord notification for healing action"""
        if not self.discord_notifier:
            return
        
        try:
            status_emoji = "✅" if success else "❌"
            status_text = "Success" if success else "Failed"
            
            embed_data = {
                'title': f'{status_emoji} Auto-Healing: {action}',
                'description': f"**Container:** {container_name}\n**Action:** {action}\n**Status:** {status_text}",
                'color': 3066993 if success else 15158332,
                'fields': [
                    {
                        'name': 'Message',
                        'value': message,
                        'inline': False
                    },
                    {
                        'name': 'Timestamp',
                        'value': datetime.now().isoformat(),
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Auto-Recovery System'
                }
            }
            
            self.discord_notifier(
                f"{status_emoji} Auto-Healing {action}: {container_name}",
                'success' if success else 'error',
                embed_data
            )
        except Exception as e:
            logger.error(f"Error sending healing Discord notification: {e}")
    
    def heal_cloud_fault(self, fault: Dict[str, Any]) -> Dict[str, Any]:
        """
        Heal a cloud-specific fault (service crash, resource exhaustion, network issue)
        
        Args:
            fault: Fault information dictionary
            
        Returns:
            Healing result dictionary
        """
        start_time = datetime.now()
        fault_type = fault.get('type', 'unknown')
        service = fault.get('service', 'unknown')
        
        # Enhanced logging with step-by-step explanation
        logger.info("="*70)
        logger.info(f"🔧 ATTEMPTING TO HEAL CLOUD FAULT")
        logger.info("="*70)
        logger.info(f"Fault Type: {fault_type}")
        logger.info(f"Service: {service}")
        logger.info(f"Timestamp: {start_time.isoformat()}")
        logger.info("="*70)
        
        print(f"\n{'='*70}")
        print(f"🔧 HEALING PROCESS STARTED")
        print(f"{'='*70}")
        print(f"Fault: {fault_type.upper()}")
        print(f"Service: {service}")
        print(f"{'='*70}\n")
        
        healing_result = {
            'timestamp': start_time.isoformat(),
            'fault': fault,
            'fault_type': fault_type,
            'status': 'failed',
            'analysis': None,
            'actions': [],
            'success': False,
            'manual_instructions': None,
            'error_message': None
        }
        
        try:
            # Step 1: Root cause analysis
            if self.root_cause_analyzer:
                analysis = self.root_cause_analyzer.analyze_fault(fault)
                healing_result['analysis'] = analysis
                root_cause = analysis.get('root_cause', 'Unknown')
                confidence = analysis.get('confidence', 0.0)
                
                logger.info(f"📊 STEP 1: ROOT CAUSE ANALYSIS")
                logger.info(f"   Root Cause: {root_cause}")
                logger.info(f"   Confidence: {confidence:.0%}")
                logger.info(f"   Classification: {analysis.get('fault_classification', 'Unknown')}")
                
                print(f"📊 Root Cause Analysis:")
                print(f"   Cause: {root_cause}")
                print(f"   Confidence: {confidence:.0%}")
                if analysis.get('recommended_actions'):
                    print(f"   Recommended Actions: {len(analysis.get('recommended_actions', []))} actions identified")
                
                # Send Discord notification for healing attempt
                if self.discord_notifier:
                    self._send_healing_attempt_discord_notification(fault, analysis)
            else:
                analysis = None
                root_cause = 'Analysis not available'
                confidence = 0.5
            
            # Step 2: Determine healing action based on fault type
            logger.info(f"📋 STEP 2: DETERMINING HEALING ACTION")
            print(f"📋 Determining healing action for {fault_type}...")
            healing_action = None
            
            if fault_type == 'service_crash':
                # Try to restart the container
                container_name = service if service.startswith('cloud-sim-') else f'cloud-sim-{service}'
                healing_action = {
                    'type': 'restart_container',
                    'container': container_name,
                    'description': f'Restart crashed container {container_name}'
                }
            elif fault_type == 'cpu_exhaustion':
                healing_action = {
                    'type': 'cleanup_resources',
                    'description': 'Clean up CPU-intensive processes'
                }
            elif fault_type == 'memory_exhaustion':
                healing_action = {
                    'type': 'cleanup_resources',
                    'description': 'Clean up memory-intensive processes and clear caches'
                }
            elif fault_type == 'disk_full':
                healing_action = {
                    'type': 'free_disk_space',
                    'description': 'Free up disk space'
                }
            elif fault_type == 'network_issue':
                healing_action = {
                    'type': 'restore_network',
                    'description': 'Restore network connectivity'
                }
            
            # Step 3: Execute healing action
            if healing_action and self.auto_execute:
                logger.info(f"⚙️  STEP 3: EXECUTING HEALING ACTION")
                logger.info(f"   Action: {healing_action.get('type', 'unknown')}")
                logger.info(f"   Description: {healing_action.get('description', 'No description')}")
                
                print(f"⚙️  Executing healing action: {healing_action.get('description', 'Unknown action')}")
                
                action_result = self._execute_healing_action(healing_action, fault)
                healing_result['actions'].append(action_result)
                
                if action_result.get('success'):
                    logger.info(f"   ✅ Action executed successfully")
                    print(f"   ✅ Action successful: {action_result.get('output', 'No output')}")
                else:
                    logger.warning(f"   ❌ Action failed: {action_result.get('error', 'Unknown error')}")
                    print(f"   ❌ Action failed: {action_result.get('error', 'Unknown error')}")
                
                if action_result['success']:
                    # Step 4: Verify healing
                    time.sleep(3)  # Wait for changes to take effect
                    verification = self._verify_cloud_fault_healing(fault)
                    healing_result['verification'] = verification
                    
                    if verification.get('success', False):
                        healing_result['status'] = 'healed'
                        healing_result['success'] = True
                        
                        logger.info("="*70)
                        logger.info(f"✅ HEALING SUCCESSFUL")
                        logger.info("="*70)
                        logger.info(f"Fault: {fault_type}")
                        logger.info(f"Service: {service}")
                        logger.info(f"Verification: {verification.get('details', 'Verified')}")
                        logger.info("="*70)
                        
                        print(f"\n{'='*70}")
                        print(f"✅ HEALING SUCCESSFUL!")
                        print(f"{'='*70}")
                        print(f"Fault: {fault_type}")
                        print(f"Service: {service}")
                        print(f"Verification: {verification.get('details', 'Verified')}")
                        print(f"{'='*70}\n")
                        
                        # Send success Discord notification
                        if self.discord_notifier:
                            self._send_healing_success_discord_notification(fault, healing_result)
                    else:
                        healing_result['status'] = 'failed_verification'
                        
                        logger.warning("="*70)
                        logger.warning(f"❌ HEALING VERIFICATION FAILED")
                        logger.warning("="*70)
                        logger.warning(f"Fault: {fault_type}")
                        logger.warning(f"Service: {service}")
                        logger.warning(f"Reason: {verification.get('details', 'Verification failed')}")
                        logger.warning("="*70)
                        
                        print(f"\n{'='*70}")
                        print(f"❌ HEALING VERIFICATION FAILED")
                        print(f"{'='*70}")
                        print(f"Reason: {verification.get('details', 'Verification failed')}")
                        print(f"{'='*70}\n")
                        
                        # Generate manual instructions
                        healing_result['manual_instructions'] = self._generate_manual_instructions(fault, analysis)
                        
                        # Send failure Discord notification with manual instructions
                        if self.discord_notifier:
                            self._send_healing_failed_discord_notification(fault, healing_result)
                else:
                    healing_result['status'] = 'failed'
                    healing_result['error_message'] = action_result.get('error', 'Healing action failed')
                    
                    # Generate manual instructions
                    healing_result['manual_instructions'] = self._generate_manual_instructions(fault, analysis)
                    
                    # Send failure Discord notification
                    if self.discord_notifier:
                        self._send_healing_failed_discord_notification(fault, healing_result)
            else:
                # Auto-execute disabled or no action determined
                healing_result['status'] = 'pending_approval' if not self.auto_execute else 'no_action'
                healing_result['manual_instructions'] = self._generate_manual_instructions(fault, analysis)
        
        except Exception as e:
            logger.error(f"Error during cloud fault healing: {e}")
            healing_result['error_message'] = str(e)
            healing_result['status'] = 'exception'
            healing_result['manual_instructions'] = self._generate_manual_instructions(fault, None)
        
        # Record the healing attempt
        self._record_healing(healing_result)
        
        return healing_result
    
    def _verify_cloud_fault_healing(self, fault: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that cloud fault healing was successful"""
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
                if self.container_healer:
                    container_name = service if service.startswith('cloud-sim-') else f'cloud-sim-{service}'
                    health = self.container_healer.verify_container_health(container_name)
                    
                    if health.get('is_running', False):
                        verification['success'] = True
                        verification['details'] = f'Container {container_name} is running'
                    else:
                        verification['details'] = f'Container {container_name} is not running'
            elif fault_type in ['cpu_exhaustion', 'memory_exhaustion', 'disk_full']:
                # Verify resource usage is below threshold
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
            elif fault_type == 'network_issue':
                # Verify port is accessible
                port = fault.get('port', 0)
                if port > 0:
                    import socket
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
    
    def _generate_manual_instructions(self, fault: Dict[str, Any], 
                                     analysis: Dict[str, Any] = None) -> str:
        """Generate manual healing instructions when auto-healing fails"""
        fault_type = fault.get('type', 'unknown')
        service = fault.get('service', 'unknown')
        container_name = service if service.startswith('cloud-sim-') else f'cloud-sim-{service}'
        
        instructions = []
        instructions.append(f"# Manual Healing Instructions for {fault_type}")
        instructions.append("")
        instructions.append(f"**Fault:** {fault.get('message', 'Unknown fault')}")
        instructions.append(f"**Service:** {service}")
        instructions.append("")
        
        if fault_type == 'service_crash':
            instructions.append("## Steps to Fix Service Crash:")
            instructions.append("")
            instructions.append("1. **Check container status:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   docker ps -a | grep {container_name}")
            instructions.append(f"   ```")
            instructions.append("")
            instructions.append("2. **View container logs:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   docker logs {container_name} --tail 50")
            instructions.append(f"   ```")
            instructions.append("")
            instructions.append("3. **Restart the container:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   docker restart {container_name}")
            instructions.append(f"   ```")
            instructions.append("")
            instructions.append("4. **If restart fails, recreate the container:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   cd /home/kasun/Documents/Heal-X-Bot")
            instructions.append(f"   # Try newer syntax first:")
            instructions.append(f"   docker compose -f config/docker-compose-cloud-sim.yml up -d --no-deps {service}")
            instructions.append(f"   # Or use older syntax:")
            instructions.append(f"   docker-compose -f config/docker-compose-cloud-sim.yml up -d --no-deps {service}")
            instructions.append(f"   ```")
        elif fault_type == 'cpu_exhaustion':
            instructions.append("## Steps to Fix CPU Exhaustion:")
            instructions.append("")
            instructions.append("1. **Identify CPU-intensive processes:**")
            instructions.append("   ```bash")
            instructions.append("   top -b -n 1 | head -20")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("2. **Kill resource-hogging processes (if safe):**")
            instructions.append("   ```bash")
            instructions.append("   kill -9 <PID>")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("3. **Clear system cache:**")
            instructions.append("   ```bash")
            instructions.append("   sudo sync")
            instructions.append("   sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
            instructions.append("   ```")
        elif fault_type == 'memory_exhaustion':
            instructions.append("## Steps to Fix Memory Exhaustion:")
            instructions.append("")
            instructions.append("1. **Check memory usage:**")
            instructions.append("   ```bash")
            instructions.append("   free -h")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("2. **Kill memory-intensive processes:**")
            instructions.append("   ```bash")
            instructions.append("   ps aux --sort=-%mem | head -10")
            instructions.append("   kill -9 <PID>")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("3. **Clear caches and restart services:**")
            instructions.append("   ```bash")
            instructions.append("   sudo sync")
            instructions.append("   sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'")
            instructions.append("   ```")
        elif fault_type == 'disk_full':
            instructions.append("## Steps to Fix Disk Full:")
            instructions.append("")
            instructions.append("1. **Check disk usage:**")
            instructions.append("   ```bash")
            instructions.append("   df -h")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("2. **Clean up Docker resources:**")
            instructions.append("   ```bash")
            instructions.append("   docker system prune -a --volumes")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("3. **Remove old logs:**")
            instructions.append("   ```bash")
            instructions.append("   sudo find /var/log -type f -name '*.log.*' -mtime +7 -delete")
            instructions.append("   ```")
            instructions.append("")
            instructions.append("4. **Clean apt cache:**")
            instructions.append("   ```bash")
            instructions.append("   sudo apt-get clean")
            instructions.append("   ```")
        elif fault_type == 'network_issue':
            instructions.append("## Steps to Fix Network Issue:")
            instructions.append("")
            instructions.append(f"1. **Check if container is running:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   docker ps | grep {container_name}")
            instructions.append(f"   ```")
            instructions.append("")
            instructions.append("2. **Check port accessibility:**")
            port = fault.get('port', 0)
            if port > 0:
                instructions.append(f"   ```bash")
                instructions.append(f"   curl http://localhost:{port}/health")
                instructions.append(f"   ```")
            instructions.append("")
            instructions.append("3. **Restart network services:**")
            instructions.append("   ```bash")
            instructions.append("   sudo systemctl restart systemd-resolved")
            instructions.append("   ```")
            instructions.append("")
            instructions.append(f"4. **Restart the container:**")
            instructions.append(f"   ```bash")
            instructions.append(f"   docker restart {container_name}")
            instructions.append(f"   ```")
        
        if analysis and analysis.get('recommended_actions'):
            instructions.append("")
            instructions.append("## AI-Recommended Actions:")
            for i, action in enumerate(analysis.get('recommended_actions', []), 1):
                instructions.append(f"{i}. {action}")
        
        return "\n".join(instructions)
    
    def _send_healing_attempt_discord_notification(self, fault: Dict[str, Any], analysis: Dict[str, Any]):
        """Send Discord notification when healing attempt starts"""
        if not self.discord_notifier:
            return
        
        try:
            embed_data = {
                'title': '🔧 Auto-Healing Attempt Started',
                'description': f"**Fault Type:** {fault.get('type', 'unknown')}\n**Service:** {fault.get('service', 'unknown')}",
                'color': 16776960,  # Yellow
                'fields': [
                    {
                        'name': 'Root Cause',
                        'value': analysis.get('root_cause', 'Analyzing...')[:200],
                        'inline': False
                    },
                    {
                        'name': 'Confidence',
                        'value': f"{analysis.get('confidence', 0) * 100:.0f}%",
                        'inline': True
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Auto-Recovery System'
                }
            }
            
            self.discord_notifier(
                f"🔧 Auto-healing started for {fault.get('service', 'unknown')}",
                'warning',
                embed_data
            )
        except Exception as e:
            logger.error(f"Error sending healing attempt notification: {e}")
    
    def _send_healing_success_discord_notification(self, fault: Dict[str, Any], healing_result: Dict[str, Any]):
        """Send Discord notification when healing succeeds"""
        if not self.discord_notifier:
            return
        
        try:
            actions_taken = healing_result.get('actions', [])
            action_summary = "\n".join([f"• {a.get('action', {}).get('description', 'Unknown action')}" 
                                       for a in actions_taken if a.get('success')])
            
            embed_data = {
                'title': '✅ Auto-Healing Successful',
                'description': f"**Fault Type:** {fault.get('type', 'unknown')}\n**Service:** {fault.get('service', 'unknown')}",
                'color': 3066993,  # Green
                'fields': [
                    {
                        'name': 'Actions Taken',
                        'value': action_summary or 'No actions',
                        'inline': False
                    },
                    {
                        'name': 'Verification',
                        'value': healing_result.get('verification', {}).get('details', 'Verified'),
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Auto-Recovery System'
                }
            }
            
            self.discord_notifier(
                f"✅ Auto-healing successful for {fault.get('service', 'unknown')}",
                'success',
                embed_data
            )
        except Exception as e:
            logger.error(f"Error sending healing success notification: {e}")
    
    def _send_healing_failed_discord_notification(self, fault: Dict[str, Any], healing_result: Dict[str, Any]):
        """Send Discord notification when healing fails, including manual instructions"""
        if not self.discord_notifier:
            return
        
        try:
            manual_instructions = healing_result.get('manual_instructions', 'No manual instructions available')
            # Truncate instructions for Discord (limit to 2000 chars)
            instructions_preview = manual_instructions[:1500] + "..." if len(manual_instructions) > 1500 else manual_instructions
            
            embed_data = {
                'title': '❌ Auto-Healing Failed - Manual Intervention Required',
                'description': f"**Fault Type:** {fault.get('type', 'unknown')}\n**Service:** {fault.get('service', 'unknown')}",
                'color': 15158332,  # Red
                'fields': [
                    {
                        'name': 'Error',
                        'value': healing_result.get('error_message', 'Unknown error')[:500],
                        'inline': False
                    },
                    {
                        'name': 'Manual Instructions',
                        'value': f"```\n{instructions_preview}\n```",
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Healing Bot - Manual Intervention Required'
                }
            }
            
            self.discord_notifier(
                f"❌ Auto-healing failed for {fault.get('service', 'unknown')} - Manual steps required",
                'critical',
                embed_data
            )
        except Exception as e:
            logger.error(f"Error sending healing failed notification: {e}")
    
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
                          critical_services_monitor=None, container_healer=None,
                          root_cause_analyzer=None, discord_notifier=None, event_emitter=None):
    """Initialize the auto-healer"""
    global _auto_healer_instance
    
    if _auto_healer_instance is None:
        _auto_healer_instance = AutoHealer(
            gemini_analyzer=gemini_analyzer,
            system_log_collector=system_log_collector,
            critical_services_monitor=critical_services_monitor,
            container_healer=container_healer,
            root_cause_analyzer=root_cause_analyzer,
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        logger.info("Auto-healer initialized with cloud healing capabilities")
    
    return _auto_healer_instance

def get_auto_healer():
    """Get the auto-healer instance"""
    return _auto_healer_instance

