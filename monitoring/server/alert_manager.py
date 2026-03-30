"""
Alert Manager to track Discord alerts sent by the system
"""
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DiscordAlertManager:
    """
    Manages history of alerts sent to Discord
    """
    
    def __init__(self, max_alerts: int = 100):
        self.alerts: List[Dict[str, Any]] = []
        self.max_alerts = max_alerts
        logger.info(f"Discord Alert Manager initialized (max_alerts: {max_alerts})")
    
    def record_alert(self, message: str, severity: str = "info", embed_data: Optional[Dict[str, Any]] = None):
        """
        Record an alert to the history
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'severity': severity.upper(),
            'embed_data': embed_data,
            'source': 'discord_notification'
        }
        
        # Add to list
        self.alerts.append(alert)
        
        # Maintain max size (sliding window)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
            
        logger.debug(f"Recorded Discord alert: {message[:50]}...")
    
    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alerts sorted by timestamp (newest first)
        """
        # Sort by timestamp descending
        sorted_alerts = sorted(
            self.alerts,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        return sorted_alerts[:limit]
    
    def clear_alerts(self):
        """Clear all alerts from history"""
        self.alerts.clear()
        logger.info("Discord alerts history cleared")

# Singleton instance
_instance = None

def get_discord_alert_manager(max_alerts: int = 100) -> DiscordAlertManager:
    global _instance
    if _instance is None:
        _instance = DiscordAlertManager(max_alerts)
    return _instance
