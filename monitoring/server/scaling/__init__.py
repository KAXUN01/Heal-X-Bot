"""
Automatic Scaling Module
Monitors server resources and manages automatic scaling with admin approval
"""

from .scaling_monitor import ScalingMonitor
from .scaling_manager import ScalingManager
from .docker_compose_manager import DockerComposeManager
from .scaling_history import ScalingHistory

__all__ = [
    'ScalingMonitor',
    'ScalingManager',
    'DockerComposeManager',
    'ScalingHistory'
]

