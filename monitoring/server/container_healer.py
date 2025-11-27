"""
Container Healer - Docker Container Recovery Module
Handles container restart, recovery, and health restoration
"""

import subprocess
import logging
import time
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import docker
from docker.errors import DockerException, APIError

logger = logging.getLogger(__name__)

class ContainerHealer:
    """Handle container recovery and healing actions"""
    
    def __init__(self, discord_notifier=None, event_emitter=None):
        """
        Initialize container healer
        
        Args:
            discord_notifier: Function to send Discord notifications
            event_emitter: Function to emit events for dashboard
        """
        self.docker_client = None
        self.discord_notifier = discord_notifier
        self.event_emitter = event_emitter
        
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized for container healer")
        except DockerException as e:
            logger.warning(f"Docker client not available: {e}")
            self.docker_client = None
    
    def restart_container(self, container_name: str) -> Tuple[bool, str]:
        """
        Restart a stopped or crashed container
        
        Args:
            container_name: Name of the container to restart
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Check current status
            status = container.status
            
            # Restart the container
            container.restart(timeout=30)
            
            # Wait a moment for container to start
            time.sleep(2)
            
            # Verify it's running
            container.reload()
            if container.status == 'running':
                message = f"Container {container_name} restarted successfully"
                logger.info(f"✅ {message}")
                
                # Send Discord notification
                if self.discord_notifier:
                    self._send_healing_notification(
                        container_name,
                        'restart',
                        True,
                        message
                    )
                
                # Emit event
                if self.event_emitter:
                    self.event_emitter({
                        'event_type': 'healing_action',
                        'action': 'restart_container',
                        'container': container_name,
                        'status': 'success',
                        'timestamp': datetime.now().isoformat()
                    })
                
                return True, message
            else:
                message = f"Container {container_name} restart failed - status: {container.status}"
                logger.warning(f"❌ {message}")
                return False, message
                
        except docker.errors.NotFound:
            message = f"Container {container_name} not found"
            logger.error(message)
            return False, message
        except Exception as e:
            message = f"Error restarting container {container_name}: {str(e)}"
            logger.error(message)
            return False, message
    
    def start_container(self, container_name: str) -> Tuple[bool, str]:
        """
        Start a stopped container
        
        Args:
            container_name: Name of the container to start
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            container.start()
            
            # Wait and verify
            time.sleep(2)
            container.reload()
            
            if container.status == 'running':
                message = f"Container {container_name} started successfully"
                logger.info(f"✅ {message}")
                
                if self.discord_notifier:
                    self._send_healing_notification(
                        container_name,
                        'start',
                        True,
                        message
                    )
                
                return True, message
            else:
                return False, f"Container {container_name} start failed - status: {container.status}"
                
        except Exception as e:
            message = f"Error starting container {container_name}: {str(e)}"
            logger.error(message)
            return False, message
    
    def stop_container(self, container_name: str) -> Tuple[bool, str]:
        """
        Stop a running container (for controlled shutdown)
        
        Args:
            container_name: Name of the container to stop
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            container.stop(timeout=30)
            message = f"Container {container_name} stopped successfully"
            logger.info(f"✅ {message}")
            return True, message
        except Exception as e:
            message = f"Error stopping container {container_name}: {str(e)}"
            logger.error(message)
            return False, message
    
    def recreate_container(self, container_name: str) -> Tuple[bool, str]:
        """
        Recreate a container (stop, remove, and start again)
        
        Args:
            container_name: Name of the container to recreate
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_client:
            return False, "Docker client not available"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Get container image
            image = container.image.tags[0] if container.image.tags else None
            if not image:
                return False, f"Cannot recreate {container_name}: image not found"
            
            # Stop and remove
            try:
                container.stop(timeout=10)
            except:
                pass  # May already be stopped
            
            container.remove()
            
            # Recreate using docker compose (newer syntax) or docker-compose (older syntax)
            # Try newer syntax first
            try:
                result = subprocess.run(
                    ['docker', 'compose', '-f', 'config/docker-compose-cloud-sim.yml', 'up', '-d', '--no-deps', container_name],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd='/home/kasun/Documents/Heal-X-Bot'
                )
                
                if result.returncode == 0:
                    message = f"Container {container_name} recreated successfully"
                    logger.info(f"✅ {message}")
                    
                    if self.discord_notifier:
                        self._send_healing_notification(
                            container_name,
                            'recreate',
                            True,
                            message
                        )
                    
                    return True, message
                else:
                    raise FileNotFoundError  # Fall through to docker-compose
            except FileNotFoundError:
                # Try with docker-compose (older syntax)
                try:
                    result = subprocess.run(
                        ['docker-compose', '-f', 'config/docker-compose-cloud-sim.yml', 'up', '-d', '--no-deps', container_name],
                        capture_output=True,
                        text=True,
                        timeout=60,
                        cwd='/home/kasun/Documents/Heal-X-Bot'
                    )
                    
                    if result.returncode == 0:
                        message = f"Container {container_name} recreated successfully"
                        logger.info(f"✅ {message}")
                        return True, message
                    else:
                        return False, f"Failed to recreate container: {result.stderr}"
                except:
                    return False, "Docker compose not available for container recreation"
        except Exception as e:
            message = f"Error recreating container {container_name}: {str(e)}"
            logger.error(message)
            return False, message
    
    def verify_container_health(self, container_name: str) -> Dict[str, Any]:
        """
        Verify container is healthy after healing
        
        Args:
            container_name: Name of the container to verify
            
        Returns:
            Health verification result
        """
        if not self.docker_client:
            return {
                'healthy': False,
                'error': 'Docker client not available'
            }
        
        try:
            container = self.docker_client.containers.get(container_name)
            container.reload()
            
            verification = {
                'container': container_name,
                'timestamp': datetime.now().isoformat(),
                'status': container.status,
                'healthy': False,
                'is_running': container.status == 'running',
                'health_status': container.attrs['State'].get('Health', {}).get('Status', 'unknown')
            }
            
            # Check if running
            if verification['is_running']:
                # Check health status if available
                if verification['health_status'] == 'healthy':
                    verification['healthy'] = True
                elif verification['health_status'] == 'starting':
                    verification['healthy'] = None  # Unknown, still starting
                else:
                    verification['healthy'] = False
            else:
                verification['healthy'] = False
            
            return verification
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def _send_healing_notification(self, container_name: str, action: str, 
                                   success: bool, message: str):
        """Send Discord notification for healing action"""
        if not self.discord_notifier:
            return
        
        try:
            status_emoji = "✅" if success else "❌"
            status_text = "Success" if success else "Failed"
            
            embed_data = {
                'title': f'{status_emoji} Container Healing: {action}',
                'description': f"**Container:** {container_name}\n**Action:** {action}\n**Status:** {status_text}",
                'color': 3066993 if success else 15158332,  # Green or Red
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
                f"{status_emoji} Container {action}: {container_name}",
                'success' if success else 'error',
                embed_data
            )
        except Exception as e:
            logger.error(f"Error sending healing notification: {e}")


# Singleton instance
_container_healer_instance = None

def initialize_container_healer(discord_notifier=None, event_emitter=None) -> ContainerHealer:
    """Initialize the container healer"""
    global _container_healer_instance
    
    if _container_healer_instance is None:
        _container_healer_instance = ContainerHealer(
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        logger.info("Container healer initialized")
    
    return _container_healer_instance

def get_container_healer() -> Optional[ContainerHealer]:
    """Get the container healer instance"""
    return _container_healer_instance

