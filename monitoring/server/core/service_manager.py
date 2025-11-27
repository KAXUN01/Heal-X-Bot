"""
Unified service manager for Heal-X-Bot
Handles service initialization, dependency management, and health checking
"""
import logging
import requests
import time
from typing import Dict, Any, Optional, List, Callable
from .config import get_config
from .exceptions import ServiceError

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages service initialization and health checking"""
    
    def __init__(self, config=None):
        """Initialize service manager
        
        Args:
            config: Configuration instance (optional, will load if not provided)
        """
        self.config = config or get_config()
        self.services: Dict[str, Any] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.initialized = False
    
    def register_service(self, name: str, service: Any, health_check: Optional[Callable] = None):
        """Register a service
        
        Args:
            name: Service name
            service: Service instance
            health_check: Optional health check function
        """
        self.services[name] = service
        if health_check:
            self.health_checks[name] = health_check
        logger.debug(f"Service registered: {name}")
    
    def initialize_monitoring_services(self) -> Dict[str, Any]:
        """Initialize all monitoring services
        
        Returns:
            Dictionary of initialized services
        """
        if self.initialized:
            logger.warning("Services already initialized")
            return self.services
        
        logger.info("Initializing monitoring services...")
        
        try:
            # Initialize Gemini AI log analyzer
            try:
                from gemini_log_analyzer import initialize_gemini_analyzer
                gemini_analyzer = initialize_gemini_analyzer()
                self.register_service('gemini_analyzer', gemini_analyzer)
                logger.info("✅ Gemini AI log analyzer initialized")
            except Exception as e:
                logger.warning(f"⚠️  Gemini analyzer not available: {e}")
                gemini_analyzer = None
            
            # Initialize system-wide log collector
            try:
                from system_log_collector import initialize_system_log_collector
                system_log_collector = initialize_system_log_collector()
                self.register_service('system_log_collector', system_log_collector)
                logger.info("✅ System-wide log collector initialized")
            except Exception as e:
                logger.warning(f"⚠️  System log collector not available: {e}")
                system_log_collector = None
            
            # Initialize critical services monitor
            try:
                from critical_services_monitor import initialize_critical_services_monitor
                critical_services_monitor = initialize_critical_services_monitor()
                self.register_service('critical_services_monitor', critical_services_monitor)
                logger.info("✅ Critical services monitor initialized")
            except Exception as e:
                logger.warning(f"⚠️  Critical services monitor not available: {e}")
                critical_services_monitor = None
            
            # Initialize cloud simulation components (optional)
            container_healer = None
            root_cause_analyzer = None
            fault_detector = None
            
            try:
                from container_healer import initialize_container_healer
                from root_cause_analyzer import initialize_root_cause_analyzer
                from fault_detector import initialize_fault_detector
                
                # Discord notifier function
                def discord_notifier(message, severity="info", embed_data=None):
                    try:
                        import requests
                        discord_webhook = self.config.discord_webhook
                        if discord_webhook:
                            payload = {"content": message}
                            if embed_data:
                                payload["embeds"] = [embed_data]
                            requests.post(discord_webhook, json=payload, timeout=10)
                    except:
                        pass  # Fail silently if Discord not configured
                
                # Initialize container healer
                container_healer = initialize_container_healer(
                    discord_notifier=discord_notifier
                )
                self.register_service('container_healer', container_healer)
                
                # Initialize root cause analyzer
                root_cause_analyzer = initialize_root_cause_analyzer(
                    gemini_analyzer=gemini_analyzer
                )
                self.register_service('root_cause_analyzer', root_cause_analyzer)
                
                # Initialize fault detector
                fault_detector = initialize_fault_detector(
                    discord_notifier=discord_notifier
                )
                fault_detector.start_monitoring(interval=30)
                self.register_service('fault_detector', fault_detector)
                logger.info("✅ Cloud simulation components initialized")
            except Exception as e:
                logger.warning(f"⚠️  Cloud simulation components not available: {e}")
            
            # Initialize auto-healer
            try:
                from ..healing import initialize_auto_healer
                auto_healer = initialize_auto_healer(
                    gemini_analyzer=gemini_analyzer,
                    system_log_collector=system_log_collector,
                    critical_services_monitor=critical_services_monitor,
                    container_healer=container_healer,
                    root_cause_analyzer=root_cause_analyzer,
                    discord_notifier=discord_notifier if container_healer else None
                )
                auto_healer.start_monitoring(interval_seconds=60)
                self.register_service('auto_healer', auto_healer)
                logger.info("✅ AI-powered auto-healer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize auto-healer: {e}")
                auto_healer = None
            
            self.initialized = True
            logger.info("✅ All monitoring services initialized")
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise ServiceError(f"Failed to initialize services: {e}")
        
        return self.services
    
    def get_service(self, name: str) -> Optional[Any]:
        """Get a service by name
        
        Args:
            name: Service name
        
        Returns:
            Service instance or None if not found
        """
        return self.services.get(name)
    
    def check_service_health(self, name: str, timeout: int = 5) -> bool:
        """Check if a service is healthy
        
        Args:
            name: Service name
            timeout: Timeout in seconds
        
        Returns:
            True if healthy, False otherwise
        """
        if name in self.health_checks:
            try:
                return self.health_checks[name]()
            except:
                return False
        
        # Default health check for HTTP services
        service_configs = {
            'model': {'url': f'http://localhost:{self.config.model_port}/health'},
            'dashboard': {'url': f'http://localhost:{self.config.dashboard_port}/api/health'},
            'monitoring_server': {'url': f'http://localhost:{self.config.monitoring_server_port}/health'},
            'healing_dashboard': {'url': f'http://localhost:{self.config.healing_dashboard_port}/api/health'},
        }
        
        if name in service_configs:
            try:
                response = requests.get(
                    service_configs[name]['url'],
                    timeout=timeout
                )
                return response.status_code == 200
            except:
                return False
        
        return False
    
    def check_all_services_health(self) -> Dict[str, bool]:
        """Check health of all registered services
        
        Returns:
            Dictionary mapping service names to health status
        """
        health_status = {}
        for name in self.services.keys():
            health_status[name] = self.check_service_health(name)
        return health_status
    
    def wait_for_service(self, name: str, max_attempts: int = 30, interval: int = 2) -> bool:
        """Wait for a service to become healthy
        
        Args:
            name: Service name
            max_attempts: Maximum number of attempts
            interval: Seconds between attempts
        
        Returns:
            True if service became healthy, False otherwise
        """
        for attempt in range(max_attempts):
            if self.check_service_health(name):
                logger.info(f"✅ Service {name} is healthy")
                return True
            logger.debug(f"Waiting for {name}... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(interval)
        
        logger.warning(f"⚠️  Service {name} did not become healthy within timeout")
        return False
    
    def shutdown(self):
        """Shutdown all services gracefully"""
        logger.info("Shutting down services...")
        
        # Stop auto-healer monitoring if running
        auto_healer = self.get_service('auto_healer')
        if auto_healer and hasattr(auto_healer, 'stop_monitoring'):
            auto_healer.stop_monitoring()
        
        # Stop fault detector if running
        fault_detector = self.get_service('fault_detector')
        if fault_detector and hasattr(fault_detector, 'stop_monitoring'):
            fault_detector.stop_monitoring()
        
        self.services.clear()
        self.health_checks.clear()
        self.initialized = False
        logger.info("✅ All services shut down")


# Global service manager instance
_service_manager_instance: Optional[ServiceManager] = None


def get_service_manager(config=None) -> ServiceManager:
    """Get global service manager instance (singleton)
    
    Args:
        config: Configuration instance (optional)
    
    Returns:
        ServiceManager instance
    """
    global _service_manager_instance
    
    if _service_manager_instance is None:
        _service_manager_instance = ServiceManager(config)
    
    return _service_manager_instance

