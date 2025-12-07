"""
Scaling Manager - Manage scaling templates and execute scaling
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .docker_compose_manager import DockerComposeManager
from .scaling_history import ScalingHistory

logger = logging.getLogger(__name__)

class ScalingManager:
    """Manage scaling templates and execute scaling operations"""
    
    def __init__(
        self,
        templates_file: Optional[str] = None,
        compose_file: Optional[str] = None,
        history: Optional[ScalingHistory] = None
    ):
        """
        Initialize scaling manager
        
        Args:
            templates_file: Path to scaling templates JSON file
            compose_file: Path to docker-compose.yml
            history: ScalingHistory instance
        """
        if templates_file:
            self.templates_file = Path(templates_file)
        else:
            self.templates_file = Path(__file__).parent.parent.parent.parent / 'config' / 'scaling_templates.json'
        
        self.compose_manager = DockerComposeManager(compose_file)
        self.history = history or ScalingHistory()
        
        # Pending scaling suggestions
        self.pending_suggestions: Dict[str, Dict[str, Any]] = {}
        
        # Load templates
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load scaling templates from file"""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    templates_list = data.get('templates', [])
                    # Convert list to dict by ID
                    self.templates = {t['id']: t for t in templates_list}
                logger.info(f"Loaded {len(self.templates)} scaling templates")
            else:
                logger.warning(f"Templates file not found: {self.templates_file}")
                # Create default templates
                self._create_default_templates()
        except Exception as e:
            logger.error(f"Error loading templates: {e}")
            self._create_default_templates()
    
    def _save_templates(self):
        """Save templates to file"""
        try:
            self.templates_file.parent.mkdir(parents=True, exist_ok=True)
            templates_list = list(self.templates.values())
            data = {
                'last_updated': datetime.now().isoformat(),
                'templates': templates_list
            }
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.templates)} templates")
        except Exception as e:
            logger.error(f"Error saving templates: {e}")
    
    def _create_default_templates(self):
        """Create default scaling templates"""
        default_templates = [
            {
                'id': 'low',
                'name': 'Low Resources',
                'description': 'Minimal resource allocation for resource-constrained systems',
                'cpu_cores': 1,
                'memory_gb': 2,
                'services': {
                    'model': {'cpus': '0.5', 'memory': '1G'},
                    'server': {'cpus': '0.5', 'memory': '512M'}
                }
            },
            {
                'id': 'medium',
                'name': 'Medium Resources',
                'description': 'Balanced resource allocation (recommended)',
                'cpu_cores': 2,
                'memory_gb': 4,
                'services': {
                    'model': {'cpus': '1', 'memory': '2G'},
                    'server': {'cpus': '1', 'memory': '1G'}
                }
            },
            {
                'id': 'high',
                'name': 'High Resources',
                'description': 'Maximum resource allocation for high-performance systems',
                'cpu_cores': 4,
                'memory_gb': 8,
                'services': {
                    'model': {'cpus': '2', 'memory': '4G'},
                    'server': {'cpus': '1', 'memory': '2G'}
                }
            }
        ]
        
        for template in default_templates:
            self.templates[template['id']] = template
        
        self._save_templates()
        logger.info("Created default scaling templates")
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all scaling templates"""
        return list(self.templates.values())
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID"""
        return self.templates.get(template_id)
    
    def create_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new scaling template
        
        Args:
            template: Template dictionary with id, name, description, cpu_cores, memory_gb, services
        
        Returns:
            Created template
        """
        template_id = template.get('id')
        if not template_id:
            raise ValueError("Template must have an 'id' field")
        
        if template_id in self.templates:
            raise ValueError(f"Template with id '{template_id}' already exists")
        
        # Validate template structure
        required_fields = ['name', 'cpu_cores', 'memory_gb', 'services']
        for field in required_fields:
            if field not in template:
                raise ValueError(f"Template must have '{field}' field")
        
        self.templates[template_id] = template
        self._save_templates()
        
        logger.info(f"Created template: {template_id}")
        return template
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing template
        
        Args:
            template_id: ID of template to update
            updates: Dictionary with fields to update
        
        Returns:
            Updated template
        """
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
        
        template = self.templates[template_id]
        template.update(updates)
        self._save_templates()
        
        logger.info(f"Updated template: {template_id}")
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template
        
        Args:
            template_id: ID of template to delete
        
        Returns:
            True if deleted
        """
        if template_id not in self.templates:
            return False
        
        # Don't allow deleting default templates
        if template_id in ['low', 'medium', 'high']:
            raise ValueError(f"Cannot delete default template: {template_id}")
        
        del self.templates[template_id]
        self._save_templates()
        
        logger.info(f"Deleted template: {template_id}")
        return True
    
    def create_scaling_suggestion(
        self,
        template_id: str,
        reason: str,
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a scaling suggestion
        
        Args:
            template_id: ID of template to suggest
            reason: Reason for suggestion
            metrics: Current resource metrics
        
        Returns:
            Suggestion dictionary
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        suggestion_id = f"suggestion-{datetime.now().timestamp()}"
        suggestion = {
            'id': suggestion_id,
            'template_id': template_id,
            'template_name': template['name'],
            'reason': reason,
            'metrics': metrics,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'services': template.get('services', {})
        }
        
        self.pending_suggestions[suggestion_id] = suggestion
        
        # Add to history
        self.history.add_event(
            event_type='suggestion',
            status='pending',
            template_id=template_id,
            template_name=template['name'],
            details={
                'reason': reason,
                'metrics': metrics
            },
            triggered_by='system'
        )
        
        logger.info(f"Created scaling suggestion: {suggestion_id}")
        return suggestion
    
    def approve_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        """
        Approve and execute a scaling suggestion
        
        Args:
            suggestion_id: ID of suggestion to approve
        
        Returns:
            Execution result
        """
        if suggestion_id not in self.pending_suggestions:
            raise ValueError(f"Suggestion '{suggestion_id}' not found")
        
        suggestion = self.pending_suggestions[suggestion_id]
        template_id = suggestion['template_id']
        template = self.get_template(template_id)
        
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        # Execute scaling
        result = self.execute_scaling(template_id, triggered_by='approval')
        
        # Update suggestion
        suggestion['status'] = 'approved'
        suggestion['executed_at'] = datetime.now().isoformat()
        suggestion['result'] = result
        
        # Remove from pending
        del self.pending_suggestions[suggestion_id]
        
        # Add to history
        self.history.add_event(
            event_type='approval',
            status='completed',
            template_id=template_id,
            template_name=template['name'],
            details={'suggestion_id': suggestion_id, 'result': result},
            triggered_by='admin'
        )
        
        logger.info(f"Approved and executed suggestion: {suggestion_id}")
        return result
    
    def reject_suggestion(self, suggestion_id: str, reason: Optional[str] = None):
        """
        Reject a scaling suggestion
        
        Args:
            suggestion_id: ID of suggestion to reject
            reason: Optional rejection reason
        """
        if suggestion_id not in self.pending_suggestions:
            raise ValueError(f"Suggestion '{suggestion_id}' not found")
        
        suggestion = self.pending_suggestions[suggestion_id]
        template_id = suggestion['template_id']
        template = self.get_template(template_id)
        
        # Update suggestion
        suggestion['status'] = 'rejected'
        suggestion['rejected_at'] = datetime.now().isoformat()
        if reason:
            suggestion['rejection_reason'] = reason
        
        # Remove from pending
        del self.pending_suggestions[suggestion_id]
        
        # Add to history
        self.history.add_event(
            event_type='rejection',
            status='rejected',
            template_id=template_id,
            template_name=template['name'] if template else None,
            details={'suggestion_id': suggestion_id, 'reason': reason},
            triggered_by='admin'
        )
        
        logger.info(f"Rejected suggestion: {suggestion_id}")
    
    def execute_scaling(self, template_id: str, triggered_by: str = 'manual') -> Dict[str, Any]:
        """
        Execute scaling using a template
        
        Args:
            template_id: ID of template to use
            triggered_by: Who triggered the scaling (manual, approval, system)
        
        Returns:
            Execution result
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")
        
        services = template.get('services', {})
        if not services:
            raise ValueError(f"Template '{template_id}' has no services defined")
        
        try:
            # Update docker-compose.yml
            results = self.compose_manager.update_multiple_services(services)
            
            # Check if all succeeded
            all_succeeded = all(results.values())
            
            if all_succeeded:
                # Restart affected containers
                restart_results = self._restart_containers(list(services.keys()))
                
                result = {
                    'success': True,
                    'template_id': template_id,
                    'template_name': template['name'],
                    'services_updated': results,
                    'containers_restarted': restart_results,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add to history
                self.history.add_event(
                    event_type='execution',
                    status='completed',
                    template_id=template_id,
                    template_name=template['name'],
                    details=result,
                    triggered_by=triggered_by
                )
                
                logger.info(f"Scaling executed successfully: {template_id}")
            else:
                result = {
                    'success': False,
                    'template_id': template_id,
                    'error': 'Some services failed to update',
                    'services_updated': results,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add to history
                self.history.add_event(
                    event_type='execution',
                    status='failed',
                    template_id=template_id,
                    template_name=template['name'],
                    details=result,
                    triggered_by=triggered_by
                )
                
                logger.error(f"Scaling execution failed: {template_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing scaling: {e}", exc_info=True)
            result = {
                'success': False,
                'template_id': template_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to history
            self.history.add_event(
                event_type='execution',
                status='failed',
                template_id=template_id,
                template_name=template.get('name'),
                details=result,
                triggered_by=triggered_by
            )
            
            return result
    
    def _restart_containers(self, service_names: List[str]) -> Dict[str, bool]:
        """
        Restart Docker containers for services
        
        Args:
            service_names: List of service names to restart
        
        Returns:
            Dictionary mapping service names to restart success status
        """
        results = {}
        
        for service_name in service_names:
            try:
                # Map service names to container names
                container_name_map = {
                    'model': 'ddos-model',
                    'server': 'monitoring-server',
                    'incident-bot': 'incident-bot',
                    'dashboard': 'ml-dashboard',
                    'prometheus': 'prometheus'
                }
                
                container_name = container_name_map.get(service_name, service_name)
                
                # Restart container using docker command
                result = subprocess.run(
                    ['docker', 'restart', container_name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                success = result.returncode == 0
                results[service_name] = success
                
                if success:
                    logger.info(f"Restarted container: {container_name}")
                else:
                    logger.warning(f"Failed to restart container {container_name}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error restarting container for {service_name}: {e}")
                results[service_name] = False
        
        return results
    
    def get_pending_suggestions(self) -> List[Dict[str, Any]]:
        """Get all pending scaling suggestions"""
        return list(self.pending_suggestions.values())
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """
        Get current scaling status
        
        Returns:
            Dictionary with scaling status
        """
        return {
            'pending_suggestions': len(self.pending_suggestions),
            'templates_count': len(self.templates),
            'pending_suggestions_list': self.get_pending_suggestions()
        }

