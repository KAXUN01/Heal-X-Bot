"""
Resource management healing actions
"""
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any
from .base import HealingActionResult

logger = logging.getLogger(__name__)


class ResourceHealingActions:
    """Resource management healing actions"""
    
    def cleanup_resources(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
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
                sync_result = subprocess.run(
                    ['sudo', 'sync'], 
                    timeout=10, 
                    check=False, 
                    capture_output=True, 
                    text=True
                )
                drop_cache_result = subprocess.run(
                    ['sudo', 'sh', '-c', 'echo 3 > /proc/sys/vm/drop_caches'], 
                    timeout=10, 
                    check=False,
                    capture_output=True,
                    text=True
                )
                if sync_result.returncode == 0 and drop_cache_result.returncode == 0:
                    cleaned.append('System cache cleared')
                else:
                    logger.warning(f"Cache clear warnings - sync: {sync_result.stderr}, drop: {drop_cache_result.stderr}")
            except subprocess.TimeoutExpired:
                logger.warning("Cache clear operations timed out")
            except Exception as e:
                logger.warning(f"Error clearing cache: {e}")
            
            if cleaned:
                message = f"Resource cleanup: {', '.join(cleaned)}"
                logger.info(f"✅ {message}")
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=message
                )
            else:
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output="No resource cleanup needed"
                )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error cleaning up resources: {str(e)}"
            )
    
    def restore_network(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
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
                return HealingActionResult(
                    action=cmd_info,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    output=message
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
                error=f"Error restoring network: {str(e)}"
            )

