"""
Notification Manager for CPU/Memory Hog Detection
Manages notification cooldowns and prevents spam to Discord
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages notification state and enforces cooldown periods"""
    
    def __init__(self, 
                 default_cooldown_minutes: int = 15,
                 severity_cooldowns: Optional[Dict[str, int]] = None,
                 max_retention_hours: int = 24):
        """
        Initialize NotificationManager
        
        Args:
            default_cooldown_minutes: Default cooldown in minutes for notifications
            severity_cooldowns: Dict mapping severity to cooldown minutes
                e.g., {"critical": 5, "error": 10, "warning": 15}
            max_retention_hours: Maximum hours to retain notification history
        """
        self.default_cooldown_minutes = default_cooldown_minutes
        self.max_retention_hours = max_retention_hours
        
        # Default severity cooldowns if not provided
        self.severity_cooldowns = severity_cooldowns or {
            "critical": 5,
            "error": 10,
            "warning": 15,
            "info": 15
        }
        
        # Track notifications: {process_key: {resource_type: {last_notified_time, last_value, last_severity}}}
        self.notification_history: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    def get_severity(self, value: float, threshold: float) -> str:
        """
        Determine severity based on how much over threshold
        
        Args:
            value: Current resource usage value
            threshold: Threshold value
            
        Returns:
            Severity level: "warning", "error", or "critical"
        """
        over_threshold = value - threshold
        threshold_range = threshold * 0.1  # 10% of threshold as range
        
        if over_threshold >= threshold_range * 0.9:  # 99%+ of threshold
            return "critical"
        elif over_threshold >= threshold_range * 0.5:  # 95-99% of threshold
            return "error"
        else:  # 90-95% of threshold
            return "warning"
    
    def _get_cooldown_seconds(self, severity: str) -> int:
        """Get cooldown period in seconds for given severity"""
        cooldown_minutes = self.severity_cooldowns.get(severity, self.default_cooldown_minutes)
        return cooldown_minutes * 60
    
    def should_notify(self, 
                     process_key: str, 
                     resource_type: str, 
                     current_value: float, 
                     threshold: float) -> Tuple[bool, Optional[str]]:
        """
        Check if notification should be sent
        
        Args:
            process_key: Unique identifier for process (e.g., "1234_process_name")
            resource_type: Type of resource ("cpu" or "memory")
            current_value: Current resource usage value
            threshold: Threshold value
            
        Returns:
            Tuple of (should_notify: bool, reason: Optional[str])
            reason can be: "first_detection", "cooldown_expired", "severity_increased", or None
        """
        # Determine current severity
        current_severity = self.get_severity(current_value, threshold)
        
        # Check if we have history for this process+resource
        if process_key not in self.notification_history:
            # First time detecting this process
            return True, "first_detection"
        
        if resource_type not in self.notification_history[process_key]:
            # First time detecting this resource type for this process
            return True, "first_detection"
        
        history = self.notification_history[process_key][resource_type]
        last_notified_time = history.get("last_notified_time")
        last_severity = history.get("last_severity")
        last_value = history.get("last_value", 0)
        
        if last_notified_time is None:
            return True, "first_detection"
        
        # Check if severity increased
        severity_levels = {"warning": 1, "error": 2, "critical": 3}
        current_level = severity_levels.get(current_severity, 0)
        last_level = severity_levels.get(last_severity, 0)
        
        if current_level > last_level:
            # Severity increased, always notify
            return True, "severity_increased"
        
        # Check if cooldown expired
        cooldown_seconds = self._get_cooldown_seconds(last_severity)
        time_since_notification = (datetime.now() - last_notified_time).total_seconds()
        
        if time_since_notification >= cooldown_seconds:
            return True, "cooldown_expired"
        
        # Don't notify - still in cooldown and severity hasn't increased
        return False, None
    
    def record_notification(self, 
                           process_key: str, 
                           resource_type: str, 
                           value: float, 
                           severity: str):
        """
        Record that a notification was sent
        
        Args:
            process_key: Unique identifier for process
            resource_type: Type of resource ("cpu" or "memory")
            value: Resource usage value at time of notification
            severity: Severity level of notification
        """
        if process_key not in self.notification_history:
            self.notification_history[process_key] = {}
        
        if resource_type not in self.notification_history[process_key]:
            self.notification_history[process_key][resource_type] = {}
        
        self.notification_history[process_key][resource_type] = {
            "last_notified_time": datetime.now(),
            "last_value": value,
            "last_severity": severity
        }
    
    def cleanup_old_entries(self):
        """Remove notification history entries older than max_retention_hours"""
        if not self.notification_history:
            return
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_retention_hours)
        removed_count = 0
        
        # Iterate over a copy of keys to avoid modification during iteration
        process_keys = list(self.notification_history.keys())
        
        for process_key in process_keys:
            resource_types = list(self.notification_history[process_key].keys())
            
            for resource_type in resource_types:
                history = self.notification_history[process_key][resource_type]
                last_notified_time = history.get("last_notified_time")
                
                if last_notified_time and last_notified_time < cutoff_time:
                    # Remove this resource type entry
                    del self.notification_history[process_key][resource_type]
                    removed_count += 1
            
            # Remove process key if no resource types left
            if not self.notification_history[process_key]:
                del self.notification_history[process_key]
        
        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} old notification history entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about notification history"""
        total_processes = len(self.notification_history)
        total_entries = sum(
            len(resources) 
            for resources in self.notification_history.values()
        )
        
        return {
            "total_tracked_processes": total_processes,
            "total_notification_entries": total_entries,
            "max_retention_hours": self.max_retention_hours,
            "default_cooldown_minutes": self.default_cooldown_minutes,
            "severity_cooldowns": self.severity_cooldowns
        }

