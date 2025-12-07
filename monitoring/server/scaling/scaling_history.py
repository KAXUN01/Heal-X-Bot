"""
Scaling History - Track scaling events
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import deque

logger = logging.getLogger(__name__)

class ScalingHistory:
    """Track and manage scaling event history"""
    
    def __init__(self, history_file: Optional[str] = None, max_in_memory: int = 100):
        """
        Initialize scaling history
        
        Args:
            history_file: Path to JSON file for persistent storage
            max_in_memory: Maximum events to keep in memory
        """
        self.history_file = history_file or str(
            Path(__file__).parent.parent.parent.parent / 'config' / 'scaling_history.json'
        )
        self.max_in_memory = max_in_memory
        self.history: deque = deque(maxlen=max_in_memory)
        self._load_history()
    
    def _load_history(self):
        """Load history from file"""
        try:
            history_path = Path(self.history_file)
            if history_path.exists():
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    # Load last max_in_memory events
                    events = data.get('events', [])
                    for event in events[-self.max_in_memory:]:
                        self.history.append(event)
                logger.info(f"Loaded {len(self.history)} scaling events from history")
        except Exception as e:
            logger.warning(f"Could not load scaling history: {e}")
    
    def _save_history(self):
        """Save history to file"""
        try:
            history_path = Path(self.history_file)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert deque to list for JSON serialization
            events = list(self.history)
            data = {
                'last_updated': datetime.now().isoformat(),
                'events': events
            }
            
            with open(history_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save scaling history: {e}")
    
    def add_event(
        self,
        event_type: str,
        status: str,
        template_id: Optional[str] = None,
        template_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        triggered_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Add a scaling event to history
        
        Args:
            event_type: Type of event (suggestion, approval, rejection, manual, execution)
            status: Event status (pending, approved, rejected, completed, failed)
            template_id: ID of scaling template used
            template_name: Name of scaling template
            details: Additional event details
            triggered_by: Who triggered the event (system, admin, manual)
        
        Returns:
            Created event dictionary
        """
        event = {
            'id': f"event-{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'status': status,
            'template_id': template_id,
            'template_name': template_name,
            'triggered_by': triggered_by,
            'details': details or {}
        }
        
        self.history.append(event)
        self._save_history()
        
        logger.info(f"Added scaling event: {event_type} - {status}")
        return event
    
    def get_history(self, limit: Optional[int] = None, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get scaling history
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
        
        Returns:
            List of event dictionaries
        """
        events = list(self.history)
        
        # Filter by type if specified
        if event_type:
            events = [e for e in events if e.get('type') == event_type]
        
        # Reverse to show newest first
        events.reverse()
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        return events
    
    def get_latest_event(self, event_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest scaling event
        
        Args:
            event_type: Filter by event type
        
        Returns:
            Latest event dictionary or None
        """
        events = self.get_history(limit=1, event_type=event_type)
        return events[0] if events else None
    
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self._save_history()
        logger.info("Scaling history cleared")

