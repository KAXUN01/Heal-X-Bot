"""
Centralized configuration management for Heal-X-Bot
Loads and validates environment variables with defaults
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from .exceptions import ConfigurationError

# Global config instance
_config_instance: Optional['Config'] = None


class Config:
    """Centralized configuration manager"""
    
    def __init__(self, env_path: Optional[Path] = None):
        """Initialize configuration
        
        Args:
            env_path: Path to .env file. If None, searches for .env in project root
        """
        # Load .env file
        if env_path is None:
            # Search for .env in project root (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent.parent
            env_path = project_root / '.env'
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        
        # AI Configuration
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Slack/Discord Integration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK')
        self.discord_webhook = os.getenv('DISCORD_WEBHOOK') or os.getenv('DISCORD_WEBHOOK_URL')
        
        # AWS S3 Configuration
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        self.s3_log_prefix = os.getenv('S3_LOG_PREFIX', 'incident-bot-logs/')
        self.s3_upload_interval = int(os.getenv('S3_UPLOAD_INTERVAL', '300'))
        
        # Port Configuration
        self.model_port = int(os.getenv('MODEL_PORT', '8080'))
        self.dashboard_port = int(os.getenv('DASHBOARD_PORT', '5001'))  # Using healing dashboard port
        self.network_analyzer_port = int(os.getenv('NETWORK_ANALYZER_PORT', '8000'))
        self.incident_bot_port = int(os.getenv('INCIDENT_BOT_PORT', '8000'))
        self.monitoring_server_port = int(os.getenv('MONITORING_SERVER_PORT', '5000'))
        self.healing_dashboard_port = int(os.getenv('HEALING_DASHBOARD_PORT', '5001'))
        
        # Service URLs
        self.model_url = os.getenv('MODEL_URL', f'http://localhost:{self.model_port}')
        self.network_analyzer_url = os.getenv('NETWORK_ANALYZER_URL', 
                                             f'http://localhost:{self.network_analyzer_port}')
        self.monitoring_server_url = os.getenv('MONITORING_SERVER_URL',
                                              f'http://localhost:{self.monitoring_server_port}')
        
        # Self-Healing Configuration
        self.self_healing_enabled = os.getenv('SELF_HEALING_ENABLED', 'false').lower() == 'true'
        self.self_healing_confidence_threshold = float(
            os.getenv('SELF_HEALING_CONFIDENCE_THRESHOLD', '0.8')
        )
        
        # Grafana Configuration
        self.grafana_admin_password = os.getenv('GRAFANA_ADMIN_PASSWORD', 'admin')
        
        # Project paths
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.logs_dir = self.project_root / 'logs'
        self.config_dir = self.project_root / 'config'
        self.data_dir = self.project_root / 'data'
        
    def validate(self, required_keys: Optional[list] = None) -> bool:
        """Validate configuration
        
        Args:
            required_keys: List of required configuration keys. 
                          If None, only checks for GEMINI_API_KEY
        
        Returns:
            True if valid, raises ConfigurationError if invalid
        """
        if required_keys is None:
            required_keys = []
        
        errors = []
        
        # Check for required API keys if specified
        if 'gemini_api_key' in required_keys and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY or GOOGLE_API_KEY is required but not set")
        
        if 'discord_webhook' in required_keys and not self.discord_webhook:
            errors.append("DISCORD_WEBHOOK is required but not set")
        
        if 'aws_credentials' in required_keys:
            if not self.aws_access_key_id or not self.aws_secret_access_key:
                errors.append("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required but not set")
        
        if errors:
            raise ConfigurationError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return True
    
    def get_port(self, service: str) -> int:
        """Get port for a service
        
        Args:
            service: Service name (model, dashboard, network-analyzer, etc.)
        
        Returns:
            Port number
        """
        port_map = {
            'model': self.model_port,
            'dashboard': self.dashboard_port,
            'network-analyzer': self.network_analyzer_port,
            'incident-bot': self.incident_bot_port,
            'monitoring-server': self.monitoring_server_port,
            'healing-dashboard': self.healing_dashboard_port,
        }
        return port_map.get(service.lower(), 5000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for logging/debugging)
        
        Returns:
            Configuration as dictionary (sensitive values masked)
        """
        return {
            'gemini_api_key': '***' if self.gemini_api_key else None,
            'slack_webhook': '***' if self.slack_webhook else None,
            'discord_webhook': '***' if self.discord_webhook else None,
            'aws_region': self.aws_region,
            's3_bucket_name': self.s3_bucket_name,
            'model_port': self.model_port,
            'dashboard_port': self.dashboard_port,
            'network_analyzer_port': self.network_analyzer_port,
            'monitoring_server_port': self.monitoring_server_port,
            'healing_dashboard_port': self.healing_dashboard_port,
            'self_healing_enabled': self.self_healing_enabled,
            'self_healing_confidence_threshold': self.self_healing_confidence_threshold,
            'project_root': str(self.project_root),
        }


def get_config(env_path: Optional[Path] = None, force_reload: bool = False) -> Config:
    """Get global configuration instance (singleton)
    
    Args:
        env_path: Path to .env file
        force_reload: Force reload configuration even if already loaded
    
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None or force_reload:
        _config_instance = Config(env_path)
    
    return _config_instance

