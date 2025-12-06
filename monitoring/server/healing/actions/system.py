"""
System-level healing actions
"""
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any
from .base import BaseHealingAction, HealingActionResult

logger = logging.getLogger(__name__)


class SystemHealingActions:
    """System-level healing actions"""
    
    # Safe services that can be restarted
    SAFE_SERVICES = ['docker', 'apache2', 'nginx', 'systemd-resolved', 'cron', 'ssh']
    
    # Safe directories for permission fixes
    SAFE_DIRS = ['/usr/local/bin', '/var/log', '/opt', '/home']
    
    def restart_service(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Safely restart a system service"""
        service = cmd_info.get('service', '')
        
        # Safety check: Only restart safe services
        if not any(safe_svc in service for safe_svc in self.SAFE_SERVICES):
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Service {service} not in safe restart list"
            )
        
        try:
            # Use systemctl to restart
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', service],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=f"Service {service} restarted successfully"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Failed to restart {service}: {result.stderr}"
                )
        except subprocess.TimeoutExpired:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Timeout restarting {service}"
            )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error restarting {service}: {str(e)}"
            )
    
    def fix_permissions(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Fix file permissions"""
        file_path = cmd_info.get('path', '')
        
        # Safety check: Only fix permissions in safe directories
        if not any(file_path.startswith(safe_dir) for safe_dir in self.SAFE_DIRS):
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Path {file_path} not in safe directories"
            )
        
        try:
            # Make file executable
            result = subprocess.run(
                ['sudo', 'chmod', '+x', file_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=f"Fixed permissions for {file_path}"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Failed to fix permissions: {result.stderr}"
                )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error fixing permissions: {str(e)}"
            )
    
    def clear_cache(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Clear system or service cache"""
        try:
            # Clear system cache (safe operation)
            try:
                sync_result = subprocess.run(['sudo', 'sync'], timeout=10, capture_output=True, text=True, check=False)
                if sync_result.returncode != 0:
                    logger.warning(f"Sync command returned non-zero: {sync_result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Sync command timed out")
            except Exception as e:
                logger.warning(f"Error running sync: {e}")
            
            try:
                drop_cache_result = subprocess.run(
                    ['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                    timeout=10, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if drop_cache_result.returncode != 0:
                    logger.warning(f"Drop caches command returned non-zero: {drop_cache_result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Drop caches command timed out")
            except Exception as e:
                logger.warning(f"Error dropping caches: {e}")
            
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=True,
                output="System cache cleared"
            )
        except Exception as e:
            logger.error(f"Unexpected error clearing cache: {e}", exc_info=True)
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error clearing cache: {str(e)}"
            )
    
    def rotate_logs(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
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
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=f"Logs rotated for {service}"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Failed to rotate logs: {result.stderr}"
                )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error rotating logs: {str(e)}"
            )
    
    def free_disk_space(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Free up disk space by cleaning old files"""
        try:
            cleaned = []
            errors = []
            
            # Clean apt cache
            try:
                apt_result = subprocess.run(
                    ['sudo', 'apt-get', 'clean'], 
                    timeout=30, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if apt_result.returncode == 0:
                    cleaned.append('apt cache')
                else:
                    errors.append(f"apt-get clean failed: {apt_result.stderr}")
            except subprocess.TimeoutExpired:
                errors.append("apt-get clean timed out")
            except Exception as e:
                errors.append(f"apt-get clean error: {str(e)}")
            
            # Clean old logs (older than 7 days)
            try:
                log_result = subprocess.run(
                    ['sudo', 'find', '/var/log', '-type', 'f', '-name', '*.log.*', '-mtime', '+7', '-delete'],
                    timeout=60,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if log_result.returncode == 0:
                    cleaned.append('old logs')
                else:
                    errors.append(f"log cleanup failed: {log_result.stderr}")
            except subprocess.TimeoutExpired:
                errors.append("log cleanup timed out")
            except Exception as e:
                errors.append(f"log cleanup error: {str(e)}")
            
            # Clean temp files
            try:
                temp_result = subprocess.run(
                    ['sudo', 'rm', '-rf', '/tmp/*'], 
                    timeout=30, 
                    capture_output=True, 
                    text=True, 
                    check=False
                )
                if temp_result.returncode == 0:
                    cleaned.append('temp files')
                else:
                    errors.append(f"temp cleanup failed: {temp_result.stderr}")
            except subprocess.TimeoutExpired:
                errors.append("temp cleanup timed out")
            except Exception as e:
                errors.append(f"temp cleanup error: {str(e)}")
            
            if cleaned:
                output = f"Freed disk space: {', '.join(cleaned)}"
                if errors:
                    output += f" (warnings: {', '.join(errors)})"
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=output
                )
            elif errors:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"All cleanup operations failed: {', '.join(errors)}"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output="No cleanup needed"
                )
        except Exception as e:
            logger.error(f"Unexpected error freeing disk space: {e}", exc_info=True)
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error freeing disk space: {str(e)}"
            )
    
    def restart_network(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Restart network services"""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'systemd-resolved'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output="Network services restarted"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Failed to restart network: {result.stderr}"
                )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error restarting network: {str(e)}"
            )
    
    def reload_config(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
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
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=f"Config reloaded for {service}"
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    error=f"Failed to reload config: {result.stderr}"
                )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error reloading config: {str(e)}"
            )
    
    def kill_zombie_process(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
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
                message = f"Found {len(zombies)} zombie processes (auto-cleanup by kernel)"
            else:
                message = "No zombie processes found"
            
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=True,
                output=message
            )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error checking zombies: {str(e)}"
            )

