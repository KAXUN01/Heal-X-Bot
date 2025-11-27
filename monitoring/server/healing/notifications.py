"""
Discord notification logic for healing actions
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


def send_healing_discord_notification(discord_notifier: Callable,
                                     container_name: str,
                                     action: str,
                                     success: bool,
                                     message: str):
    """Send Discord notification for healing action
    
    Args:
        discord_notifier: Discord notification function
        container_name: Name of the container
        action: Action performed (restart, start, recreate, etc.)
        success: Whether action succeeded
        message: Result message
    """
    if not discord_notifier:
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
        
        discord_notifier(
            f"{status_emoji} Auto-Healing {action}: {container_name}",
            'success' if success else 'error',
            embed_data
        )
    except Exception as e:
        logger.error(f"Error sending healing Discord notification: {e}")


def send_healing_attempt_notification(discord_notifier: Callable,
                                     fault: Dict[str, Any],
                                     analysis: Dict[str, Any]):
    """Send Discord notification when healing attempt starts
    
    Args:
        discord_notifier: Discord notification function
        fault: Fault information dictionary
        analysis: Root cause analysis dictionary
    """
    if not discord_notifier:
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
        
        discord_notifier(
            f"🔧 Auto-healing started for {fault.get('service', 'unknown')}",
            'warning',
            embed_data
        )
    except Exception as e:
        logger.error(f"Error sending healing attempt notification: {e}")


def send_healing_success_notification(discord_notifier: Callable,
                                     fault: Dict[str, Any],
                                     healing_result: Dict[str, Any]):
    """Send Discord notification when healing succeeds
    
    Args:
        discord_notifier: Discord notification function
        fault: Fault information dictionary
        healing_result: Healing result dictionary
    """
    if not discord_notifier:
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
        
        discord_notifier(
            f"✅ Auto-healing successful for {fault.get('service', 'unknown')}",
            'success',
            embed_data
        )
    except Exception as e:
        logger.error(f"Error sending healing success notification: {e}")


def send_healing_failed_notification(discord_notifier: Callable,
                                    fault: Dict[str, Any],
                                    healing_result: Dict[str, Any]):
    """Send Discord notification when healing fails, including manual instructions
    
    Args:
        discord_notifier: Discord notification function
        fault: Fault information dictionary
        healing_result: Healing result dictionary
    """
    if not discord_notifier:
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
        
        discord_notifier(
            f"❌ Auto-healing failed for {fault.get('service', 'unknown')} - Manual steps required",
            'critical',
            embed_data
        )
    except Exception as e:
        logger.error(f"Error sending healing failed notification: {e}")

