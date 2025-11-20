"""
AI-Powered Auto-Healing System Orchestrator
Main orchestration logic for the auto-healing system
"""
import re
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from .actions.system import SystemHealingActions
from .actions.container import ContainerHealingActions
from .actions.resource import ResourceHealingActions
from .verification import verify_healing, verify_cloud_fault_healing
from .notifications import (
    send_healing_attempt_notification,
    send_healing_success_notification,
    send_healing_failed_notification
)
from .instructions import generate_manual_instructions
from .history import HealingHistory

logger = logging.getLogger(__name__)

# Singleton instance
_auto_healer_instance: Optional['AutoHealer'] = None


class AutoHealer:
    """
    AI-Powered Auto-Healing System
    
    Features:
    - Detects critical errors automatically
    - Uses AI to analyze and suggest fixes
    - Executes safe remediation actions
    - Verifies fixes worked
    - Logs all healing actions
    """
    
    def __init__(self, gemini_analyzer=None, system_log_collector=None, 
                 critical_services_monitor=None, container_healer=None,
                 root_cause_analyzer=None, discord_notifier=None, event_emitter=None):
        """Initialize AutoHealer
        
        Args:
            gemini_analyzer: Gemini AI analyzer instance
            system_log_collector: System log collector instance
            critical_services_monitor: Critical services monitor instance
            container_healer: Container healer instance
            root_cause_analyzer: Root cause analyzer instance
            discord_notifier: Discord notification function
            event_emitter: Event emitter instance
        """
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
        self.monitoring_interval = 60  # Default monitoring interval in seconds
        
        # Initialize action handlers
        self.system_actions = SystemHealingActions()
        self.container_actions = ContainerHealingActions(
            container_healer=container_healer,
            discord_notifier=discord_notifier
        )
        self.resource_actions = ResourceHealingActions()
        
        # Map action types to handlers
        self.action_handlers = {
            'restart_service': self.system_actions.restart_service,
            'fix_permissions': self.system_actions.fix_permissions,
            'clear_cache': self.system_actions.clear_cache,
            'rotate_logs': self.system_actions.rotate_logs,
            'free_disk_space': self.system_actions.free_disk_space,
            'restart_network': self.system_actions.restart_network,
            'reload_config': self.system_actions.reload_config,
            'kill_zombie_process': self.system_actions.kill_zombie_process,
            # Cloud-specific healing actions
            'restart_container': self.container_actions.restart_container,
            'start_container': self.container_actions.start_container,
            'recreate_container': self.container_actions.recreate_container,
            'cleanup_resources': self.resource_actions.cleanup_resources,
            'restore_network': self.resource_actions.restore_network,
        }
        
        # Initialize history manager
        self.history = HealingHistory(max_history=100)
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        logger.info("Auto-Healer initialized with cloud healing capabilities")
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start automatic error monitoring and healing"""
        if self.running:
            logger.warning("Auto-healer already running")
            return
        
        self.monitoring_interval = interval_seconds
        self.running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Auto-healer monitoring started (interval: {interval_seconds}s)")
    
    def update_config(self, enabled: Optional[bool] = None, 
                     auto_execute: Optional[bool] = None,
                     max_healing_attempts: Optional[int] = None,
                     monitoring_interval: Optional[int] = None) -> Dict[str, Any]:
        """Update auto-healer configuration
        
        Args:
            enabled: Enable/disable auto-healer
            auto_execute: Auto-execute healing or require approval
            max_healing_attempts: Maximum healing attempts per error
            monitoring_interval: Monitoring interval in seconds
            
        Returns:
            Dictionary with updated configuration
        """
        if enabled is not None:
            self.enabled = enabled
            logger.info(f"Auto-healer enabled set to: {enabled}")
        
        if auto_execute is not None:
            self.auto_execute = auto_execute
            logger.info(f"Auto-execute set to: {auto_execute}")
        
        if max_healing_attempts is not None:
            if max_healing_attempts < 1 or max_healing_attempts > 10:
                raise ValueError("max_healing_attempts must be between 1 and 10")
            self.max_healing_attempts = max_healing_attempts
            logger.info(f"Max healing attempts set to: {max_healing_attempts}")
        
        if monitoring_interval is not None:
            if monitoring_interval < 10 or monitoring_interval > 3600:
                raise ValueError("monitoring_interval must be between 10 and 3600 seconds")
            
            # If monitoring is running, restart with new interval
            was_running = self.running
            if was_running:
                self.stop_monitoring()
            
            self.monitoring_interval = monitoring_interval
            
            if was_running:
                self.start_monitoring(interval_seconds=monitoring_interval)
            
            logger.info(f"Monitoring interval set to: {monitoring_interval}s")
        
        return {
            'enabled': self.enabled,
            'auto_execute': self.auto_execute,
            'max_healing_attempts': self.max_healing_attempts,
            'monitoring_interval': self.monitoring_interval,
            'monitoring': self.running
        }
    
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
        recent_history = self.history.get_recent(limit=20)
        recent_attempts = [
            h for h in recent_history
            if h.get('error_signature') == error_signature
        ]
        
        # Don't retry if we've failed multiple times recently
        if len(recent_attempts) >= self.max_healing_attempts:
            return False
        
        return True
    
    def heal_error(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to heal an error using AI analysis
        
        Args:
            error: Error dictionary
        
        Returns:
            Healing result dictionary
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
                self.history.record(healing_result)
                return healing_result
            
            analysis = self.gemini_analyzer.analyze_log(error)
            if not analysis:
                healing_result['error_message'] = 'AI analysis failed'
                self.history.record(healing_result)
                return healing_result
            
            healing_result['analysis'] = analysis
            
            # Step 2: Extract actionable commands from AI solution
            solution = analysis.get('solution', '')
            commands = self._extract_commands(solution, error)
            
            if not commands:
                healing_result['error_message'] = 'No actionable commands found in AI solution'
                healing_result['status'] = 'no_action'
                self.history.record(healing_result)
                return healing_result
            
            # Step 3: Execute commands
            if self.auto_execute:
                for cmd_info in commands:
                    action_result = self._execute_healing_action(cmd_info, error)
                    healing_result['actions'].append(action_result.to_dict())
                    
                    if not action_result.success:
                        logger.warning(f"Action failed: {action_result.error}")
                        break
            else:
                healing_result['status'] = 'pending_approval'
                healing_result['pending_commands'] = commands
                self.history.record(healing_result)
                return healing_result
            
            # Step 4: Verify the fix worked
            time.sleep(2)  # Wait for changes to take effect
            verification = verify_healing(error, self.system_log_collector)
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
        self.history.record(healing_result)
        
        return healing_result
    
    def _extract_commands(self, solution_text: str, error: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract actionable commands from AI-generated solution
        
        Args:
            solution_text: AI-generated solution text
            error: Original error dictionary
        
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
                                error: Dict[str, Any]):
        """Execute a single healing action
        
        Args:
            cmd_info: Command information dictionary
            error: Original error dictionary
        
        Returns:
            HealingActionResult instance
        """
        action_type = cmd_info.get('type')
        
        if action_type in self.action_handlers:
            handler = self.action_handlers[action_type]
            result = handler(cmd_info)
            
            if result.success:
                logger.info(f"✅ Action succeeded: {cmd_info.get('description')}")
            else:
                logger.warning(f"❌ Action failed: {cmd_info.get('description')}")
            
            return result
        else:
            from .actions.base import HealingActionResult
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f'Unknown action type: {action_type}'
            )
    
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
                    send_healing_attempt_notification(self.discord_notifier, fault, analysis)
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
                healing_result['actions'].append(action_result.to_dict())
                
                if action_result.success:
                    logger.info(f"   ✅ Action executed successfully")
                    print(f"   ✅ Action successful: {action_result.output or 'No output'}")
                    
                    # Step 4: Verify healing
                    time.sleep(3)  # Wait for changes to take effect
                    verification = verify_cloud_fault_healing(fault, self.container_healer)
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
                            send_healing_success_notification(self.discord_notifier, fault, healing_result)
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
                        from ..core.config import get_config
                        config = get_config()
                        healing_result['manual_instructions'] = generate_manual_instructions(
                            fault, analysis, config.project_root
                        )
                        
                        # Send failure Discord notification with manual instructions
                        if self.discord_notifier:
                            send_healing_failed_notification(self.discord_notifier, fault, healing_result)
                else:
                    healing_result['status'] = 'failed'
                    healing_result['error_message'] = action_result.error or 'Healing action failed'
                    
                    # Generate manual instructions
                    from ..core.config import get_config
                    config = get_config()
                    healing_result['manual_instructions'] = generate_manual_instructions(
                        fault, analysis, config.project_root
                    )
                    
                    # Send failure Discord notification
                    if self.discord_notifier:
                        send_healing_failed_notification(self.discord_notifier, fault, healing_result)
            else:
                # Auto-execute disabled or no action determined
                healing_result['status'] = 'pending_approval' if not self.auto_execute else 'no_action'
                from ..core.config import get_config
                config = get_config()
                healing_result['manual_instructions'] = generate_manual_instructions(
                    fault, analysis, config.project_root
                )
        
        except Exception as e:
            logger.error(f"Error during cloud fault healing: {e}")
            healing_result['error_message'] = str(e)
            healing_result['status'] = 'exception'
            from ..core.config import get_config
            config = get_config()
            healing_result['manual_instructions'] = generate_manual_instructions(fault, None, config.project_root)
        
        # Record the healing attempt
        self.history.record(healing_result)
        
        return healing_result
    
    def get_healing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing history"""
        return self.history.get_recent(limit)
    
    def get_healing_statistics(self) -> Dict[str, Any]:
        """Get statistics about healing attempts"""
        return self.history.get_statistics()


def initialize_auto_healer(gemini_analyzer=None, system_log_collector=None, 
                          critical_services_monitor=None, container_healer=None,
                          root_cause_analyzer=None, discord_notifier=None, event_emitter=None):
    """Initialize the auto-healer (singleton pattern)
    
    Args:
        gemini_analyzer: Gemini AI analyzer instance
        system_log_collector: System log collector instance
        critical_services_monitor: Critical services monitor instance
        container_healer: Container healer instance
        root_cause_analyzer: Root cause analyzer instance
        discord_notifier: Discord notification function
        event_emitter: Event emitter instance
    
    Returns:
        AutoHealer instance
    """
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
    """Get the auto-healer instance
    
    Returns:
        AutoHealer instance or None if not initialized
    """
    return _auto_healer_instance

