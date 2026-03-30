"""
Docker Compose Manager - Modify docker-compose.yml resource limits
"""

import yaml
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DockerComposeManager:
    """Manage docker-compose.yml file modifications for scaling"""
    
    def __init__(self, compose_file: Optional[str] = None):
        """
        Initialize docker compose manager
        
        Args:
            compose_file: Path to docker-compose.yml file
        """
        if compose_file:
            self.compose_file = Path(compose_file)
        else:
            # Default to config/docker-compose.yml
            self.compose_file = Path(__file__).parent.parent.parent.parent / 'config' / 'docker-compose.yml'
        
        if not self.compose_file.exists():
            raise FileNotFoundError(f"Docker compose file not found: {self.compose_file}")
    
    def _backup_file(self) -> Path:
        """
        Create a backup of docker-compose.yml
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.compose_file.parent / f"docker-compose.yml.backup.{timestamp}"
        shutil.copy2(self.compose_file, backup_file)
        logger.info(f"Created backup: {backup_file}")
        return backup_file
    
    def _load_compose(self) -> Dict[str, Any]:
        """Load docker-compose.yml file"""
        try:
            with open(self.compose_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading docker-compose.yml: {e}")
            raise
    
    def _save_compose(self, data: Dict[str, Any]):
        """Save docker-compose.yml file"""
        try:
            # Create backup before saving
            self._backup_file()
            
            with open(self.compose_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"Saved docker-compose.yml")
        except Exception as e:
            logger.error(f"Error saving docker-compose.yml: {e}")
            raise
    
    def get_service_resources(self, service_name: str) -> Dict[str, Any]:
        """
        Get current resource limits for a service
        
        Args:
            service_name: Name of the service
        
        Returns:
            Dictionary with current resource limits
        """
        compose_data = self._load_compose()
        services = compose_data.get('services', {})
        
        if service_name not in services:
            return {}
        
        service = services[service_name]
        deploy = service.get('deploy', {})
        resources = deploy.get('resources', {})
        
        limits = resources.get('limits', {})
        reservations = resources.get('reservations', {})
        
        return {
            'limits': limits,
            'reservations': reservations,
            'current': {
                'cpus': limits.get('cpus', ''),
                'memory': limits.get('memory', '')
            }
        }
    
    def update_service_resources(
        self,
        service_name: str,
        cpus: Optional[str] = None,
        memory: Optional[str] = None,
        reservations_cpus: Optional[str] = None,
        reservations_memory: Optional[str] = None
    ) -> bool:
        """
        Update resource limits for a service
        
        Args:
            service_name: Name of the service
            cpus: CPU limit (e.g., "2", "1.5")
            memory: Memory limit (e.g., "4G", "512M")
            reservations_cpus: CPU reservation
            reservations_memory: Memory reservation
        
        Returns:
            True if successful
        """
        try:
            compose_data = self._load_compose()
            services = compose_data.get('services', {})
            
            if service_name not in services:
                logger.error(f"Service {service_name} not found in docker-compose.yml")
                return False
            
            service = services[service_name]
            
            # Ensure deploy section exists
            if 'deploy' not in service:
                service['deploy'] = {}
            if 'resources' not in service['deploy']:
                service['deploy']['resources'] = {}
            if 'limits' not in service['deploy']['resources']:
                service['deploy']['resources']['limits'] = {}
            if 'reservations' not in service['deploy']['resources']:
                service['deploy']['resources']['reservations'] = {}
            
            resources = service['deploy']['resources']
            
            # Update limits
            if cpus is not None:
                resources['limits']['cpus'] = cpus
            if memory is not None:
                resources['limits']['memory'] = memory
            
            # Update reservations
            if reservations_cpus is not None:
                resources['reservations']['cpus'] = reservations_cpus
            if reservations_memory is not None:
                resources['reservations']['memory'] = reservations_memory
            
            # Save changes
            self._save_compose(compose_data)
            
            logger.info(f"Updated resources for {service_name}: CPUs={cpus}, Memory={memory}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating service resources: {e}", exc_info=True)
            return False
    
    def update_multiple_services(self, service_resources: Dict[str, Dict[str, str]]) -> Dict[str, bool]:
        """
        Update resources for multiple services
        
        Args:
            service_resources: Dictionary mapping service names to resource configs
                Example: {
                    "model": {"cpus": "2", "memory": "4G"},
                    "server": {"cpus": "1", "memory": "2G"}
                }
        
        Returns:
            Dictionary mapping service names to success status
        """
        results = {}
        
        try:
            compose_data = self._load_compose()
            services = compose_data.get('services', {})
            
            for service_name, resources in service_resources.items():
                if service_name not in services:
                    logger.warning(f"Service {service_name} not found, skipping")
                    results[service_name] = False
                    continue
                
                service = services[service_name]
                
                # Ensure deploy section exists
                if 'deploy' not in service:
                    service['deploy'] = {}
                if 'resources' not in service['deploy']:
                    service['deploy']['resources'] = {}
                if 'limits' not in service['deploy']['resources']:
                    service['deploy']['resources']['limits'] = {}
                
                # Update resources
                limits = service['deploy']['resources']['limits']
                if 'cpus' in resources:
                    limits['cpus'] = resources['cpus']
                if 'memory' in resources:
                    limits['memory'] = resources['memory']
                
                results[service_name] = True
            
            # Save all changes at once
            self._save_compose(compose_data)
            logger.info(f"Updated resources for {len(results)} services")
            
        except Exception as e:
            logger.error(f"Error updating multiple services: {e}", exc_info=True)
            for service_name in service_resources.keys():
                results[service_name] = False
        
        return results
    
    def get_all_services(self) -> List[str]:
        """Get list of all service names"""
        compose_data = self._load_compose()
        return list(compose_data.get('services', {}).keys())
    
    def validate_compose_file(self) -> bool:
        """
        Validate docker-compose.yml file structure
        
        Returns:
            True if valid
        """
        try:
            compose_data = self._load_compose()
            # Basic validation
            if 'services' not in compose_data:
                logger.warning("No 'services' section in docker-compose.yml")
                return False
            return True
        except Exception as e:
            logger.error(f"Invalid docker-compose.yml: {e}")
            return False

