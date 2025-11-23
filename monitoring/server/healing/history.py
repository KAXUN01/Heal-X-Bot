"""
Healing history management
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class HealingHistory:
    """Manage healing attempt history"""
    
    def __init__(self, max_history: int = 100):
        """Initialize healing history
        
        Args:
            max_history: Maximum number of history entries to keep
        """
        self.history: List[Dict[str, Any]] = []
        self.max_history = max_history
    
    def record(self, healing_result: Dict[str, Any]):
        """Record a healing attempt in history
        
        Args:
            healing_result: Healing result dictionary
        """
        self.history.append(healing_result)
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        logger.info(f"Healing attempt recorded: {healing_result.get('status', 'unknown')}")
    
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing history
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            List of recent healing results, sorted by timestamp (newest first)
        """
        return sorted(
            self.history[-limit:],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about healing attempts
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.history)
        if total == 0:
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'pending': 0,
                'success_rate': 0
            }
        
        successful = len([h for h in self.history if h.get('status') == 'healed'])
        failed = len([h for h in self.history if h.get('status') in ['failed', 'failed_verification', 'exception']])
        pending = len([h for h in self.history if h.get('status') == 'pending_approval'])
        
        return {
            'total_attempts': total,
            'successful': successful,
            'failed': failed,
            'pending': pending,
            'success_rate': round((successful / total * 100), 1) if total > 0 else 0
        }
    
    def clear(self):
        """Clear all history"""
        self.history.clear()
        logger.info("Healing history cleared")

