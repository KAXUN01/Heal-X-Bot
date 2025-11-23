"""
Base healing action interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HealingActionResult:
    """Result of a healing action"""
    action: Dict[str, Any]
    timestamp: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'action': self.action,
            'timestamp': self.timestamp,
            'success': self.success,
            'output': self.output,
            'error': self.error
        }


class BaseHealingAction(ABC):
    """Base class for healing actions"""
    
    @abstractmethod
    def execute(self, cmd_info: Dict[str, Any], error: Dict[str, Any]) -> HealingActionResult:
        """Execute the healing action
        
        Args:
            cmd_info: Command information dictionary with type, description, etc.
            error: Original error that triggered this action
        
        Returns:
            HealingActionResult with execution results
        """
        pass
    
    @abstractmethod
    def get_action_type(self) -> str:
        """Get the action type identifier
        
        Returns:
            Action type string (e.g., 'restart_service', 'fix_permissions')
        """
        pass
    
    def create_result(self, cmd_info: Dict[str, Any], success: bool, 
                     output: str = None, error: str = None) -> HealingActionResult:
        """Create a healing action result
        
        Args:
            cmd_info: Command information
            success: Whether action succeeded
            output: Success output message
            error: Error message if failed
        
        Returns:
            HealingActionResult instance
        """
        return HealingActionResult(
            action=cmd_info,
            timestamp=datetime.now().isoformat(),
            success=success,
            output=output,
            error=error
        )

