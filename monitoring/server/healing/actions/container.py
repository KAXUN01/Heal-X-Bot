"""
Container-level healing actions
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .base import HealingActionResult

logger = logging.getLogger(__name__)


class ContainerHealingActions:
    """Container-level healing actions"""
    
    def __init__(self, container_healer=None, discord_notifier=None):
        """Initialize container healing actions
        
        Args:
            container_healer: Container healer instance
            discord_notifier: Discord notification function
        """
        self.container_healer = container_healer
        self.discord_notifier = discord_notifier
    
    def restart_container(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Restart a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container name not provided"
            )
        
        if not self.container_healer:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container healer not available"
            )
        
        try:
            success, message = self.container_healer.restart_container(container_name)
            
            # Send notification if successful
            if success and self.discord_notifier:
                self._send_notification(container_name, 'restart', True, message)
            
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=success,
                output=message if success else None,
                error=None if success else message
            )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error restarting container: {str(e)}"
            )
    
    def start_container(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Start a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container name not provided"
            )
        
        if not self.container_healer:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container healer not available"
            )
        
        try:
            success, message = self.container_healer.start_container(container_name)
            
            # Send notification if successful
            if success and self.discord_notifier:
                self._send_notification(container_name, 'start', True, message)
            
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=success,
                output=message if success else None,
                error=None if success else message
            )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error starting container: {str(e)}"
            )
    
    def recreate_container(self, cmd_info: Dict[str, Any]) -> HealingActionResult:
        """Recreate a Docker container"""
        container_name = cmd_info.get('container', '')
        if not container_name:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container name not provided"
            )
        
        if not self.container_healer:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error="Container healer not available"
            )
        
        try:
            success, message = self.container_healer.recreate_container(container_name)
            
            # Send notification if successful
            if success and self.discord_notifier:
                self._send_notification(container_name, 'recreate', True, message)
            
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=success,
                output=message if success else None,
                error=None if success else message
            )
        except Exception as e:
            return HealingActionResult(
                action=cmd_info,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=f"Error recreating container: {str(e)}"
            )
    
    def _send_notification(self, container_name: str, action: str, success: bool, message: str):
        """Send Discord notification for healing action"""
        if not self.discord_notifier:
            return
        
        try:
            from ..notifications import send_healing_discord_notification
            send_healing_discord_notification(
                self.discord_notifier,
                container_name,
                action,
                success,
                message
            )
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")

