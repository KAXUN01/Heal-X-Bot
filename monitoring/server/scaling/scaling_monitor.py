"""
Scaling Monitor - Monitor CPU/Memory for critical conditions
"""

import psutil
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from collections import deque

logger = logging.getLogger(__name__)

class ScalingMonitor:
    """Monitor system resources for critical health conditions"""
    
    def __init__(
        self,
        cpu_threshold: float = 90.0,
        memory_threshold: float = 95.0,
        critical_duration_minutes: int = 5,
        check_interval_seconds: int = 30,
        on_critical_callback: Optional[Callable] = None
    ):
        """
        Initialize scaling monitor
        
        Args:
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            critical_duration_minutes: Minutes of critical state before triggering
            check_interval_seconds: Interval between checks
            on_critical_callback: Callback function when critical condition detected
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.critical_duration_minutes = critical_duration_minutes
        self.check_interval_seconds = check_interval_seconds
        self.on_critical_callback = on_critical_callback
        
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Track critical state
        self.critical_readings: deque = deque(maxlen=1000)  # Store last 1000 readings
        self.critical_start_time: Optional[datetime] = None
        self.last_suggestion_time: Optional[datetime] = None
        self.suggestion_cooldown_minutes = 30  # Don't suggest again for 30 minutes after last suggestion
        
        # Current metrics
        self.current_metrics: Dict[str, Any] = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'is_critical': False,
            'critical_duration_seconds': 0,
            'last_check': None
        }
    
    def _check_resources(self) -> Dict[str, Any]:
        """
        Check current resource usage
        
        Returns:
            Dictionary with resource metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            is_critical = cpu_percent > self.cpu_threshold and memory_percent > self.memory_threshold
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'cpu_threshold': self.cpu_threshold,
                'memory_threshold': self.memory_threshold,
                'is_critical': is_critical,
                'timestamp': datetime.now().isoformat(),
                'memory_available_gb': memory.available / (1024 ** 3),
                'cpu_count': psutil.cpu_count()
            }
        except Exception as e:
            logger.error(f"Error checking resources: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'is_critical': False,
                'error': str(e)
            }
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Scaling monitor started")
        
        while self.is_monitoring:
            try:
                metrics = self._check_resources()
                self.current_metrics.update(metrics)
                self.current_metrics['last_check'] = datetime.now().isoformat()
                
                # Record reading
                reading = {
                    'timestamp': datetime.now(),
                    'cpu_percent': metrics['cpu_percent'],
                    'memory_percent': metrics['memory_percent'],
                    'is_critical': metrics['is_critical']
                }
                self.critical_readings.append(reading)
                
                # Check if critical
                if metrics['is_critical']:
                    if self.critical_start_time is None:
                        self.critical_start_time = datetime.now()
                        logger.warning(
                            f"Critical condition detected: CPU={metrics['cpu_percent']:.1f}%, "
                            f"Memory={metrics['memory_percent']:.1f}%"
                        )
                    
                    # Calculate duration
                    duration = (datetime.now() - self.critical_start_time).total_seconds() / 60
                    self.current_metrics['critical_duration_seconds'] = duration * 60
                    
                    # Check if duration threshold exceeded
                    if duration >= self.critical_duration_minutes:
                        # Check cooldown
                        if self.last_suggestion_time:
                            time_since_last = (datetime.now() - self.last_suggestion_time).total_seconds() / 60
                            if time_since_last < self.suggestion_cooldown_minutes:
                                logger.debug(
                                    f"Scaling suggestion skipped (cooldown): "
                                    f"{self.suggestion_cooldown_minutes - time_since_last:.1f} minutes remaining"
                                )
                            else:
                                self._trigger_critical_callback(metrics, duration)
                        else:
                            self._trigger_critical_callback(metrics, duration)
                else:
                    # Reset critical state
                    if self.critical_start_time is not None:
                        logger.info("Critical condition resolved")
                    self.critical_start_time = None
                    self.current_metrics['critical_duration_seconds'] = 0
                
                # Sleep until next check
                time.sleep(self.check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.check_interval_seconds)
    
    def _trigger_critical_callback(self, metrics: Dict[str, Any], duration: float):
        """
        Trigger callback for critical condition
        
        Args:
            metrics: Current resource metrics
            duration: Duration in minutes of critical state
        """
        if self.on_critical_callback:
            try:
                self.last_suggestion_time = datetime.now()
                self.on_critical_callback({
                    'cpu_percent': metrics['cpu_percent'],
                    'memory_percent': metrics['memory_percent'],
                    'duration_minutes': duration,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Triggered critical callback after {duration:.1f} minutes")
            except Exception as e:
                logger.error(f"Error in critical callback: {e}", exc_info=True)
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        if self.is_monitoring:
            logger.warning("Monitor already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Scaling monitor started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Scaling monitor stopped")
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status
        
        Returns:
            Dictionary with current status
        """
        # Get latest metrics
        metrics = self._check_resources()
        self.current_metrics.update(metrics)
        
        return {
            **self.current_metrics,
            'is_monitoring': self.is_monitoring,
            'critical_duration_minutes': self.critical_duration_minutes,
            'check_interval_seconds': self.check_interval_seconds,
            'has_pending_suggestion': (
                self.critical_start_time is not None and
                (datetime.now() - self.critical_start_time).total_seconds() / 60 >= self.critical_duration_minutes
            )
        }
    
    def reset_critical_state(self):
        """Reset critical state (called after suggestion is created)"""
        self.critical_start_time = None
        self.current_metrics['critical_duration_seconds'] = 0
        logger.info("Critical state reset")

