"""
Healing Bot Dashboard API
Comprehensive backend for real-time system monitoring and management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Union
import psutil
import subprocess
import asyncio
import json
import time
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict, Counter
import logging
import re
import requests
from pathlib import Path
import signal
import random
import hashlib
from dotenv import load_dotenv
from blocked_ips_db import BlockedIPsDatabase
from healing.notification_manager import NotificationManager

# Pydantic models for request validation
class BlockIPRequest(BaseModel):
    """Request model for blocking an IP address"""
    ip: str = Field(..., description="IP address to block")
    reason: Optional[str] = Field(None, description="Reason for blocking")
    threat_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Threat level (0.0-1.0)")
    
    @validator('ip')
    def validate_ip(cls, v):
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")

class CLIExecuteRequest(BaseModel):
    """Request model for CLI command execution"""
    command: str = Field(..., min_length=1, max_length=500, description="Command to execute")

class ServiceActionRequest(BaseModel):
    """Request model for service actions"""
    service: Optional[str] = Field(None, description="Service name")
    force: Optional[bool] = Field(False, description="Force action")

class ProcessKillRequest(BaseModel):
    """Request model for killing a process"""
    pid: int = Field(..., gt=0, description="Process ID to kill")
    signal: Optional[int] = Field(15, description="Signal to send (default: 15=SIGTERM)")

class GeminiAnalyzeRequest(BaseModel):
    """Request model for Gemini log analysis"""
    log_entry: Optional[Dict[str, Any]] = Field(None, description="Single log entry to analyze")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="Multiple log entries for pattern analysis")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum number of logs to analyze")
    
    @validator('log_entry', 'logs')
    def validate_logs(cls, v, values):
        """Ensure at least one log entry is provided"""
        if not v and not values.get('logs'):
            raise ValueError("Either log_entry or logs must be provided")
        return v

class DiscordConfigRequest(BaseModel):
    """Request model for Discord webhook configuration"""
    webhook_url: str = Field(..., min_length=1, description="Discord webhook URL")
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        """Validate Discord webhook URL format"""
        if not v.startswith('https://discord.com/api/webhooks/'):
            raise ValueError("Invalid Discord webhook URL format")
        return v

class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates"""
    auto_restart: Optional[bool] = None
    cpu_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    memory_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)
    disk_threshold: Optional[float] = Field(None, ge=0.0, le=100.0)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
env_path_abs = env_path.resolve()
# Convert Path to string for load_dotenv and override existing env vars
load_dotenv(dotenv_path=str(env_path_abs), override=True)
from system_log_collector import initialize_system_log_collector, get_system_log_collector
from centralized_logger import initialize_centralized_logging, centralized_logger
from critical_services_monitor import initialize_critical_services_monitor, get_critical_services_monitor
from fluent_bit_reader import initialize_fluent_bit_reader, fluent_bit_reader

# Optional Gemini analyzer (may not be available if google.generativeai is not installed)
try:
    from gemini_log_analyzer import initialize_gemini_analyzer, gemini_analyzer
    GEMINI_AVAILABLE = True
except ImportError as e:
    # Use basic logging since logger may not be initialized yet
    import logging
    _temp_logger = logging.getLogger(__name__)
    _temp_logger.warning(f"Gemini analyzer not available: {e}. AI log analysis features will be disabled.")
    GEMINI_AVAILABLE = False
    gemini_analyzer = None
    def initialize_gemini_analyzer():
        pass

# Initialize FastAPI app
app = FastAPI(title="Healing Bot Dashboard API")

# Initialize blocked IPs database
blocked_ips_db = BlockedIPsDatabase("monitoring/server/data/blocked_ips.db")

# Add CORS middleware - configurable via environment variable
# Default: allow localhost origins for development
# Set CORS_ORIGINS environment variable to specify allowed origins (comma-separated)
# Example: CORS_ORIGINS=http://localhost:5001,http://localhost:3000
cors_origins_env = os.getenv('CORS_ORIGINS', 'http://localhost:5001,http://localhost:3000,http://127.0.0.1:5001,http://127.0.0.1:3000')
# Allow all origins only in development mode
if os.getenv('FLASK_ENV', '').lower() == 'development' or os.getenv('CORS_ALLOW_ALL', 'false').lower() == 'true':
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging using standardized configuration
try:
    from monitoring.server.core.logging_config import setup_logger
    log_dir = Path(__file__).parent.parent.parent / "logs"
    logger = setup_logger(
        name=__name__,
        log_file="Healing Dashboard API.log",
        log_dir=str(log_dir),
        console_output=True
    )
except ImportError:
    # Fallback to basic logging if core module not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Log .env file status
logger.info(f"Loading .env file from: {env_path_abs}")
if env_path_abs.exists():
    logger.info(f"✅ .env file found")
else:
    logger.warning(f"⚠️  .env file not found at {env_path_abs}")

# Initialize log collectors (must be after logger is defined)
system_log_collector = None
_gemini_analyzer = None

def initialize_log_services():
    """Initialize log collection services"""
    global system_log_collector, _gemini_analyzer
    try:
        system_log_collector = initialize_system_log_collector()
        logger.info("System log collector initialized")
    except Exception as e:
        logger.warning(f"System log collector not available: {e}")
    
    try:
        # centralized_logger is a global variable from the module
        initialize_centralized_logging()
        logger.info("Centralized logger initialized")
    except Exception as e:
        logger.warning(f"Centralized logger not available: {e}")
    
    try:
        # gemini_analyzer is a global variable from the module
        initialize_gemini_analyzer()
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        logger.info("Gemini AI analyzer initialized")
    except Exception as e:
        logger.warning(f"Gemini analyzer not available: {e}")
    
    try:
        # critical_services_monitor initialization
        initialize_critical_services_monitor()
        logger.info("Critical services monitor initialized")
    except Exception as e:
        logger.warning(f"Critical services monitor not available: {e}")
    
    try:
        # Fluent Bit reader initialization
        # Use project logs directory if running locally, or container path if in container
        project_root = Path(__file__).parent.parent.parent
        default_log_path = str(project_root / 'logs' / 'fluent-bit' / 'fluent-bit-output.jsonl')
        
        # Try multiple possible paths
        possible_paths = [
            default_log_path,
            '/home/cdrditgis/Documents/Healing-bot/logs/fluent-bit/fluent-bit-output.jsonl',
            str(Path.home() / 'Documents' / 'Healing-bot' / 'logs' / 'fluent-bit' / 'fluent-bit-output.jsonl'),
            os.getenv('FLUENT_BIT_LOG_PATH', ''),
            '/var/log/fluent-bit/fluent-bit-output.jsonl'
        ]
        
        log_path = None
        for path in possible_paths:
            if path:
                # Convert to absolute path
                abs_path = str(Path(path).absolute()) if not os.path.isabs(path) else path
                if Path(abs_path).exists():
                    log_path = abs_path
                    logger.info(f"Found Fluent Bit log file at: {log_path}")
                    break
        
        if not log_path:
            # Use default even if it doesn't exist yet (Fluent Bit will create it)
            abs_default = str(Path(default_log_path).absolute())
            log_path = abs_default
            logger.info(f"Fluent Bit log file not found, will use: {log_path}")
        
        # Ensure we use absolute path
        log_path = str(Path(log_path).absolute())
        logger.info(f"Initializing Fluent Bit reader with absolute path: {log_path}")
        
        reader = initialize_fluent_bit_reader(log_path)
        if reader:
            # Force refresh to load any existing logs
            reader.refresh_logs()
            # Re-import to get updated global
            from fluent_bit_reader import fluent_bit_reader as fbr
            if fbr:
                logger.info(f"Fluent Bit reader initialized (log path: {log_path}, loaded {len(fbr.log_cache)} logs)")
            else:
                logger.warning(f"Fluent Bit reader created but global variable not set")
        else:
            logger.warning(f"Fluent Bit reader initialization returned None")
    except Exception as e:
        logger.error(f"Fluent Bit reader not available: {e}", exc_info=True)

# Initialize on startup
initialize_log_services()

# Global configuration
def load_config():
    """Load configuration from environment variables"""
    # Reload .env to ensure we have the latest values
    load_dotenv(dotenv_path=str(env_path_abs), override=True)
    
    # Check for both DISCORD_WEBHOOK and DISCORD_WEBHOOK_URL (for backward compatibility)
    discord_webhook = os.getenv("DISCORD_WEBHOOK") or os.getenv("DISCORD_WEBHOOK_URL", "")
    discord_webhook = discord_webhook.strip() if discord_webhook else ""
    # Remove quotes if present
    if discord_webhook.startswith('"') and discord_webhook.endswith('"'):
        discord_webhook = discord_webhook[1:-1]
    if discord_webhook.startswith("'") and discord_webhook.endswith("'"):
        discord_webhook = discord_webhook[1:-1]
    
    # Notification cooldown configuration
    notification_cooldown_minutes = int(os.getenv("NOTIFICATION_COOLDOWN_MINUTES", "15"))
    notification_max_retention_hours = int(os.getenv("NOTIFICATION_MAX_RETENTION_HOURS", "24"))
    
    # Severity-specific cooldowns (in minutes)
    severity_cooldowns = {
        "critical": int(os.getenv("NOTIFICATION_CRITICAL_COOLDOWN_MINUTES", "5")),
        "error": int(os.getenv("NOTIFICATION_ERROR_COOLDOWN_MINUTES", "10")),
        "warning": int(os.getenv("NOTIFICATION_WARNING_COOLDOWN_MINUTES", "15")),
        "info": int(os.getenv("NOTIFICATION_INFO_COOLDOWN_MINUTES", "15"))
    }
    
    return {
    "auto_restart": True,
    "cpu_threshold": 90.0,
    "memory_threshold": 85.0,
    "disk_threshold": 80.0,
        "discord_webhook": discord_webhook,
    "services_to_monitor": ["nginx", "mysql", "ssh", "docker", "postgresql"],
    "model_service_url": os.getenv("MODEL_SERVICE_URL", "http://localhost:8080"),
        "notification_cooldown_minutes": notification_cooldown_minutes,
        "notification_severity_cooldowns": severity_cooldowns,
        "notification_max_retention_hours": notification_max_retention_hours,
    }

CONFIG = load_config()

# Initialize notification manager for CPU/Memory hog detection
notification_manager = NotificationManager(
    default_cooldown_minutes=CONFIG["notification_cooldown_minutes"],
    severity_cooldowns=CONFIG["notification_severity_cooldowns"],
    max_retention_hours=CONFIG["notification_max_retention_hours"]
)

# Log Discord webhook status on startup
if CONFIG["discord_webhook"]:
    # Mask the webhook URL for security (show only first and last few chars)
    webhook_display = CONFIG["discord_webhook"]
    if len(webhook_display) > 50:
        webhook_display = webhook_display[:30] + "..." + webhook_display[-20:]
    logger.info(f"✅ Discord webhook loaded: {webhook_display}")
else:
    logger.warning("⚠️  Discord webhook not configured. Set DISCORD_WEBHOOK in .env file to enable notifications.")

# Service status cache
service_cache = {}
last_cleanup_time = None
last_freed_space = None  # Store last freed space in MB
ssh_attempts = defaultdict(list)
blocked_ips = set()
command_history = []
log_buffer = []

# Track notified critical errors to avoid duplicates
notified_critical_errors = set()  # Set of (service, message_hash) tuples (stable identifier)
_critical_error_notification_times = {}  # Dict of (service, message_hash) -> timestamp (for rate limiting)

# Track ignored alerts
ignored_alerts = set()  # Set of alert IDs (service, message_hash) - stable identifier

# Track last sent warnings and time-to-failure for Discord notifications
_last_sent_warnings = set()  # Set of warning types that were sent
_last_sent_warning_count = 0  # Last warning count sent
_last_sent_time_to_failure = None  # Last time-to-failure value sent
_last_warning_notification_time = None  # Last time warnings were sent
_last_time_to_failure_notification_time = None  # Last time time-to-failure was sent

# Global alert deduplication cache: (message_hash, alert_type) -> timestamp
_alert_deduplication_cache = {}  # Dict of (message_hash, alert_type) -> timestamp

# Service operation rate limiting: (service_name, operation) -> timestamp
_last_service_notifications = {}  # Dict of (service_name, operation) -> timestamp

# IP blocking deduplication: ip -> timestamp
_last_blocked_ip_notifications = {}  # Dict of ip -> timestamp

# Resource hog killing deduplication: process_name -> timestamp
_last_killed_process_notifications = {}  # Dict of process_name -> timestamp

# DDoS Detection Storage
ddos_statistics = {
    "total_detections": 0,
    "ddos_attacks": 0,
    "false_positives": 0,
    "detection_rate": 0.0,
    "attack_types": {},
    "top_source_ips": {}
}

# ML Performance History
ml_performance_history = {
    "timestamps": [],
    "accuracy": [],
    "precision": [],
    "recall": [],
    "f1_score": [],
    "prediction_times": []
}

# ============================================================================
# WebSocket Connection Management
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# ============================================================================
# System Monitoring Functions
# ============================================================================

def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        return {
            "cpu": cpu_percent,
            "memory": memory.percent,
            "disk": disk.percent,
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {}

def check_service_status(service_name: str) -> Dict[str, Any]:
    """Check if a service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        # systemctl is-active returns:
        # - exit code 0 and stdout "active" if service is running
        # - exit code non-zero if service is not running (stopped, failed, etc.)
        output = result.stdout.strip().lower()
        is_active = result.returncode == 0 and output == "active"
        
        # Determine status string
        if is_active:
            status = "running"
        elif output == "inactive":
            status = "stopped"
        elif output == "failed":
            status = "failed"
        else:
            status = "stopped"  # Default to stopped for any non-active state
        
        return {
            "name": service_name,
            "status": status,
            "active": is_active
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking service {service_name}")
        return {"name": service_name, "status": "timeout", "active": False}
    except Exception as e:
        logger.error(f"Error checking service {service_name}: {e}")
        return {"name": service_name, "status": "unknown", "active": False}

def get_all_services_status() -> List[Dict[str, Any]]:
    """Get status of all monitored services"""
    services = []
    for service in CONFIG["services_to_monitor"]:
        status = check_service_status(service)
        services.append(status)
    return services

def start_service(service_name: str) -> bool:
    """Start a service"""
    try:
        logger.info(f"▶️ Attempting to start service: {service_name}")
        
        # First try without sudo (in case user has permissions)
        result = subprocess.run(
            ["systemctl", "start", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # If that fails, try with sudo
        if result.returncode != 0:
            logger.info(f"Non-sudo start failed, trying with sudo for {service_name}")
            result = subprocess.run(
                ["sudo", "systemctl", "start", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully started {service_name}")
            log_event("info", f"Service {service_name} started successfully")
            
            # Rate limiting: only send notification if not sent in last 15 minutes
            global _last_service_notifications
            current_time = datetime.now()
            notification_key = (service_name, "start")
            
            should_send = True
            if notification_key in _last_service_notifications:
                time_since_last = (current_time - _last_service_notifications[notification_key]).total_seconds() / 60
                if time_since_last < 15:
                    should_send = False
                    logger.debug(f"Service start notification suppressed for {service_name} (sent {time_since_last:.1f} minutes ago)")
            
            if should_send:
                send_discord_alert(f"✅ Service Started: {service_name}", alert_type="service_start", skip_deduplication=True)
                _last_service_notifications[notification_key] = current_time
                
                # Clean up old entries (older than 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                _last_service_notifications = {
                    k: v for k, v in _last_service_notifications.items()
                    if v > cutoff_time
                }
            
            # Verify the service actually started
            time.sleep(1)  # Give it a moment to start
            status_check = check_service_status(service_name)
            is_active = status_check.get("active", False)
            status = status_check.get("status", "unknown")
            
            if is_active:
                logger.info(f"✅ Verified: {service_name} is now running")
            else:
                logger.warning(f"⚠️  Warning: {service_name} start command succeeded but service status is: {status}")
            
            return True
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            logger.error(f"❌ Failed to start {service_name}: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Timeout while starting service {service_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Error starting service {service_name}: {e}", exc_info=True)
        return False

def stop_service(service_name: str) -> bool:
    """Stop a service"""
    try:
        logger.info(f"⏹️ Attempting to stop service: {service_name}")
        
        # First try without sudo (in case user has permissions)
        result = subprocess.run(
            ["systemctl", "stop", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # If that fails, try with sudo
        if result.returncode != 0:
            logger.info(f"Non-sudo stop failed, trying with sudo for {service_name}")
            result = subprocess.run(
                ["sudo", "systemctl", "stop", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully stopped {service_name}")
            log_event("info", f"Service {service_name} stopped successfully")
            
            # Rate limiting: only send notification if not sent in last 15 minutes
            global _last_service_notifications
            current_time = datetime.now()
            notification_key = (service_name, "stop")
            
            should_send = True
            if notification_key in _last_service_notifications:
                time_since_last = (current_time - _last_service_notifications[notification_key]).total_seconds() / 60
                if time_since_last < 15:
                    should_send = False
                    logger.debug(f"Service stop notification suppressed for {service_name} (sent {time_since_last:.1f} minutes ago)")
            
            if should_send:
                send_discord_alert(f"⏹️ Service Stopped: {service_name}", alert_type="service_stop", skip_deduplication=True)
                _last_service_notifications[notification_key] = current_time
                
                # Clean up old entries (older than 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                _last_service_notifications = {
                    k: v for k, v in _last_service_notifications.items()
                    if v > cutoff_time
                }
            
            return True
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            logger.error(f"❌ Failed to stop {service_name}: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Timeout while stopping service {service_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Error stopping service {service_name}: {e}", exc_info=True)
        return False

def restart_service(service_name: str) -> bool:
    """Restart a failed service"""
    try:
        logger.info(f"🔄 Attempting to restart service: {service_name}")
        
        # First try without sudo (in case user has permissions)
        result = subprocess.run(
            ["systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # If that fails, try with sudo
        if result.returncode != 0:
            logger.info(f"Non-sudo restart failed, trying with sudo for {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Successfully restarted {service_name}")
            log_event("info", f"Service {service_name} restarted successfully")
            
            # Rate limiting: only send notification if not sent in last 15 minutes
            global _last_service_notifications
            current_time = datetime.now()
            notification_key = (service_name, "restart")
            
            should_send = True
            if notification_key in _last_service_notifications:
                time_since_last = (current_time - _last_service_notifications[notification_key]).total_seconds() / 60
                if time_since_last < 15:
                    should_send = False
                    logger.debug(f"Service restart notification suppressed for {service_name} (sent {time_since_last:.1f} minutes ago)")
            
            if should_send:
                send_discord_alert(f"✅ Service Restarted: {service_name}", alert_type="service_restart", skip_deduplication=True)
                _last_service_notifications[notification_key] = current_time
                
                # Clean up old entries (older than 1 hour)
                cutoff_time = current_time - timedelta(hours=1)
                _last_service_notifications = {
                    k: v for k, v in _last_service_notifications.items()
                    if v > cutoff_time
                }
            
            # Verify the service actually started
            time.sleep(1)  # Give it a moment to start
            status_check = check_service_status(service_name)
            is_active = status_check.get("active", False)
            status = status_check.get("status", "unknown")
            
            if is_active:
                logger.info(f"✅ Verified: {service_name} is now running")
            else:
                logger.warning(f"⚠️  Warning: {service_name} restart command succeeded but service status is: {status}")
            
            return True
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            logger.error(f"❌ Failed to restart {service_name}: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  Timeout while restarting service {service_name}")
        return False
    except Exception as e:
        logger.error(f"❌ Error restarting service {service_name}: {e}", exc_info=True)
        return False

# ============================================================================
# Process Management
# ============================================================================

def get_top_processes(limit: int = 10) -> List[Dict[str, Any]]:
    """Get top processes by CPU and memory usage"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0 or pinfo['memory_percent'] > 1:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu": round(pinfo['cpu_percent'], 2),
                        "memory": round(pinfo['memory_percent'], 2)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return []

def kill_resource_hog(pid: int) -> bool:
    """Kill a process by PID"""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.terminate()
        
        # Wait up to 3 seconds for termination
        proc.wait(timeout=3)
        
        logger.info(f"Killed process {proc_name} (PID: {pid})")
        log_event("warning", f"Killed resource hog: {proc_name} (PID: {pid})")
        
        # Rate limiting: only send notification if same process name hasn't been killed in last 10 minutes
        global _last_killed_process_notifications
        current_time = datetime.now()
        
        should_send = True
        if proc_name in _last_killed_process_notifications:
            time_since_last = (current_time - _last_killed_process_notifications[proc_name]).total_seconds() / 60
            if time_since_last < 10:
                should_send = False
                logger.debug(f"Resource hog kill notification suppressed for {proc_name} (sent {time_since_last:.1f} minutes ago)")
        
        if should_send:
            send_discord_alert(f"💀 Killed Resource Hog: {proc_name} (PID: {pid})", alert_type="resource_hog_kill", skip_deduplication=True)
            _last_killed_process_notifications[proc_name] = current_time
            
            # Clean up old entries (older than 1 hour)
            cutoff_time = current_time - timedelta(hours=1)
            _last_killed_process_notifications = {
                k: v for k, v in _last_killed_process_notifications.items()
                if v > cutoff_time
            }
        
        return True
    except psutil.NoSuchProcess:
        return False
    except psutil.TimeoutExpired:
        # Force kill if terminate didn't work
        try:
            proc.kill()
            return True
        except:
            return False
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

def auto_detect_resource_hogs():
    """Automatically detect and optionally kill resource hogs"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                process_key = f"{pinfo['pid']}_{pinfo['name']}"
                
                # Check CPU usage
                if pinfo['cpu_percent'] > CONFIG['cpu_threshold']:
                    should_notify, reason = notification_manager.should_notify(
                        process_key, 
                        'cpu', 
                        pinfo['cpu_percent'], 
                        CONFIG['cpu_threshold']
                    )
                    
                    if should_notify:
                        severity = notification_manager.get_severity(
                            pinfo['cpu_percent'], 
                            CONFIG['cpu_threshold']
                        )
                        logger.warning(
                            f"CPU hog detected: {pinfo['name']} ({pinfo['cpu_percent']}%) "
                            f"[Reason: {reason}, Severity: {severity}]"
                        )
                        send_discord_alert(
                            f"⚠️ CPU Hog Detected: {pinfo['name']} using {pinfo['cpu_percent']}% CPU",
                            severity=severity
                        )
                        notification_manager.record_notification(
                            process_key, 
                            'cpu', 
                            pinfo['cpu_percent'], 
                            severity
                        )
                    else:
                        # Log debug info but don't notify
                        logger.debug(
                            f"CPU hog still active: {pinfo['name']} ({pinfo['cpu_percent']}%) "
                            f"- notification suppressed (cooldown active)"
                        )
                
                # Check Memory usage
                if pinfo['memory_percent'] > CONFIG['memory_threshold']:
                    should_notify, reason = notification_manager.should_notify(
                        process_key, 
                        'memory', 
                        pinfo['memory_percent'], 
                        CONFIG['memory_threshold']
                    )
                    
                    if should_notify:
                        severity = notification_manager.get_severity(
                            pinfo['memory_percent'], 
                            CONFIG['memory_threshold']
                        )
                        logger.warning(
                            f"Memory hog detected: {pinfo['name']} ({pinfo['memory_percent']}%) "
                            f"[Reason: {reason}, Severity: {severity}]"
                        )
                        send_discord_alert(
                            f"⚠️ Memory Hog Detected: {pinfo['name']} using {pinfo['memory_percent']}% RAM",
                            severity=severity
                        )
                        notification_manager.record_notification(
                            process_key, 
                            'memory', 
                            pinfo['memory_percent'], 
                            severity
                        )
                    else:
                        # Log debug info but don't notify
                        logger.debug(
                            f"Memory hog still active: {pinfo['name']} ({pinfo['memory_percent']}%) "
                            f"- notification suppressed (cooldown active)"
                        )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Error in resource hog detection: {e}")

# ============================================================================
# SSH Intrusion Detection
# ============================================================================

def parse_ssh_logs() -> List[Dict[str, Any]]:
    """Parse SSH logs for failed attempts"""
    ssh_events = []
    
    try:
        # Check auth log
        if os.path.exists("/var/log/auth.log"):
            with open("/var/log/auth.log", "r") as f:
                lines = f.readlines()[-1000:]  # Last 1000 lines
                
                for line in lines:
                    if "Failed password" in line:
                        # Parse IP address
                        match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            ip = match.group(1)
                            timestamp = line.split()[0:3]
                            ssh_attempts[ip].append(datetime.now())
                            
                            # Check if IP should be blocked
                            if len(ssh_attempts[ip]) > 5:
                                block_ip(ip)
                            
                            ssh_events.append({
                                "ip": ip,
                                "timestamp": " ".join(timestamp),
                                "attempts": len(ssh_attempts[ip]),
                                "blocked": ip in blocked_ips
                            })
    except Exception as e:
        logger.error(f"Error parsing SSH logs: {e}")
    
    return ssh_events

def block_ip(ip: str, attack_count: int = 1, threat_level: str = "Medium", 
             attack_type: str = None, reason: str = None, blocked_by: str = "system") -> bool:
    """Block an IP address using iptables and store in database"""
    try:
        # Check if already blocked in database
        if blocked_ips_db.is_blocked(ip):
            logger.info(f"IP {ip} is already blocked, updating attack count")
            blocked_ips_db.update_attack_count(ip, attack_count)
            return True
        
        # Try to block using iptables (may fail without sudo permissions)
        iptables_success = False
        try:
            # Try without sudo first (if user has capabilities)
            result = subprocess.run(
                ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # Try with sudo
                result = subprocess.run(
                    ["sudo", "-n", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                    capture_output=True,
                    timeout=5
                )
            
            if result.returncode == 0:
                iptables_success = True
                logger.info(f"Successfully added iptables rule for {ip}")
            elif "already exists" in result.stderr.decode().lower() or "duplicate" in result.stderr.decode().lower():
                iptables_success = True
                logger.info(f"iptables rule already exists for {ip}")
            else:
                logger.warning(f"Could not add iptables rule for {ip}: {result.stderr.decode()}")
                # Continue anyway - we'll store in database for tracking
        except subprocess.TimeoutExpired:
            logger.warning(f"iptables command timed out for {ip}")
        except Exception as e:
            logger.warning(f"Could not execute iptables for {ip}: {e}")
        
        # Always store in database regardless of iptables success
        # This allows tracking and manual iptables configuration
        success = blocked_ips_db.block_ip(
            ip_address=ip,
            attack_count=attack_count,
            threat_level=threat_level,
            attack_type=attack_type,
            reason=reason or f"Blocked due to {attack_count} attacks",
            blocked_by=blocked_by
        )
        
        if success:
            # Also add to in-memory set for backwards compatibility
            blocked_ips.add(ip)
            
            logger.warning(f"Blocked IP in database: {ip} (Threat: {threat_level}, Attacks: {attack_count})")
            
            # Rate limiting: only send notification if same IP hasn't been blocked in last 60 minutes
            global _last_blocked_ip_notifications
            current_time = datetime.now()
            
            should_send = True
            if ip in _last_blocked_ip_notifications:
                time_since_last = (current_time - _last_blocked_ip_notifications[ip]).total_seconds() / 60
                if time_since_last < 60:
                    should_send = False
                    logger.debug(f"IP block notification suppressed for {ip} (sent {time_since_last:.1f} minutes ago)")
            
            if should_send:
                if iptables_success:
                    send_discord_alert(f"🚫 Blocked IP: {ip}\nThreat Level: {threat_level}\nAttacks: {attack_count}\nFirewall: Active", alert_type="ip_block", skip_deduplication=True)
                else:
                    send_discord_alert(f"🚫 Blocked IP (Database Only): {ip}\nThreat Level: {threat_level}\nAttacks: {attack_count}\nNote: Manual iptables configuration needed", alert_type="ip_block", skip_deduplication=True)
                _last_blocked_ip_notifications[ip] = current_time
                
                # Clean up old entries (older than 2 hours)
                cutoff_time = current_time - timedelta(hours=2)
                _last_blocked_ip_notifications = {
                    k: v for k, v in _last_blocked_ip_notifications.items()
                    if v > cutoff_time
                }
            
            return True
        else:
            logger.error(f"Failed to store IP {ip} in database")
            return False
            
    except Exception as e:
        logger.error(f"Error blocking IP {ip}: {e}")
        return False

def unblock_ip(ip: str, unblocked_by: str = "admin", reason: str = None) -> bool:
    """Unblock an IP address from iptables and update database"""
    try:
        # Check if blocked in database
        if not blocked_ips_db.is_blocked(ip):
            logger.warning(f"IP {ip} is not blocked in database")
            return False
        
        # Remove from iptables
        result = subprocess.run(
            ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
            timeout=5
        )
        
        # Update database even if iptables command fails (in case rule doesn't exist)
        blocked_ips_db.unblock_ip(ip, unblocked_by=unblocked_by, reason=reason)
        
        # Remove from in-memory set
        if ip in blocked_ips:
            blocked_ips.remove(ip)
        
        logger.info(f"Unblocked IP: {ip} by {unblocked_by}")
        send_discord_alert(f"✅ Unblocked IP: {ip}\nUnblocked by: {unblocked_by}")
        return True
        
    except Exception as e:
        logger.error(f"Error unblocking IP {ip}: {e}")
        return False

# ============================================================================
# Disk Cleanup
# ============================================================================

def run_disk_cleanup() -> Dict[str, Any]:
    """Run disk cleanup operations (rate limited to once per hour)"""
    global last_cleanup_time, last_freed_space
    
    # Rate limiting: Only run cleanup once per hour
    if last_cleanup_time is not None:
        time_since_last_cleanup = (datetime.now() - last_cleanup_time).total_seconds()
        if time_since_last_cleanup < 3600:  # 1 hour = 3600 seconds
            remaining_time = int(3600 - time_since_last_cleanup)
            logger.info(f"Disk cleanup skipped. Last cleanup was {int(time_since_last_cleanup)}s ago. Next cleanup available in {remaining_time}s")
            return {
                "success": False,
                "error": f"Rate limit: Cleanup can only run once per hour. Last cleanup was {int(time_since_last_cleanup)}s ago. Try again in {remaining_time}s",
                "last_cleanup": last_cleanup_time.isoformat(),
                "next_cleanup_available": (last_cleanup_time + timedelta(seconds=3600)).isoformat()
            }
    
    try:
        initial_usage = psutil.disk_usage('/')
        freed_space = 0
        
        # Clean temp files
        cleanup_commands = [
            ["sudo", "apt-get", "clean"],
            ["sudo", "apt-get", "autoclean"],
            ["sudo", "journalctl", "--vacuum-time=7d"]
        ]
        
        for cmd in cleanup_commands:
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
            except:
                pass
        
        # Clean log files
        log_dirs = ["/var/log", "/tmp"]
        for log_dir in log_dirs:
            if os.path.exists(log_dir):
                try:
                    subprocess.run(
                        ["find", log_dir, "-type", "f", "-name", "*.log.*", "-delete"],
                        capture_output=True,
                        timeout=30
                    )
                except:
                    pass
        
        final_usage = psutil.disk_usage('/')
        freed_space = (initial_usage.used - final_usage.used) / (1024 * 1024)  # MB
        
        last_cleanup_time = datetime.now()
        last_freed_space = round(freed_space, 2)  # Store freed space
        
        logger.info(f"Disk cleanup completed. Freed {freed_space:.2f} MB")
        log_event("success", f"Disk cleanup freed {freed_space:.2f} MB")
        send_discord_alert(f"🧹 Disk Cleanup Complete: Freed {freed_space:.2f} MB")
        
        return {
            "success": True,
            "freed_space": last_freed_space,
            "timestamp": last_cleanup_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error during disk cleanup: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# DDoS Detection & ML Model Integration
# ============================================================================

def fetch_ml_metrics() -> Dict[str, Any]:
    """Fetch ML model performance metrics"""
    try:
        # Try to fetch from model service (with short timeout to avoid blocking)
        response = requests.get(
            f"{CONFIG['model_service_url']}/metrics",
            timeout=1  # Reduced timeout to fail fast
        )
        
        if response.status_code == 200:
            # Parse Prometheus metrics
            metrics_text = response.text
            
            # Extract ML metrics from Prometheus format
            ml_metrics = {
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "prediction_time_ms": 5.2,
                "throughput": 192.3
            }
            
            # Parse specific metrics if available
            for line in metrics_text.split('\n'):
                if line.startswith('ml_model_accuracy'):
                    try:
                        ml_metrics['accuracy'] = float(line.split()[-1])
                    except:
                        pass
                elif line.startswith('ml_model_precision'):
                    try:
                        ml_metrics['precision'] = float(line.split()[-1])
                    except:
                        pass
                elif line.startswith('ml_model_recall'):
                    try:
                        ml_metrics['recall'] = float(line.split()[-1])
                    except:
                        pass
                elif line.startswith('ml_model_f1_score'):
                    try:
                        ml_metrics['f1_score'] = float(line.split()[-1])
                    except:
                        pass
            
            # Update history
            timestamp = datetime.now()
            ml_performance_history['timestamps'].append(timestamp.isoformat())
            ml_performance_history['accuracy'].append(ml_metrics['accuracy'])
            ml_performance_history['precision'].append(ml_metrics['precision'])
            ml_performance_history['recall'].append(ml_metrics['recall'])
            ml_performance_history['f1_score'].append(ml_metrics['f1_score'])
            ml_performance_history['prediction_times'].append(ml_metrics['prediction_time_ms'])
            
            # Keep only last 100 entries
            max_history = 100
            for key in ml_performance_history:
                if len(ml_performance_history[key]) > max_history:
                    ml_performance_history[key] = ml_performance_history[key][-max_history:]
            
            return ml_metrics
        else:
            # Return default values if service is unavailable
            return {
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "prediction_time_ms": 5.2,
                "throughput": 192.3
            }
    except Exception as e:
        logger.error(f"Error fetching ML metrics: {e}")
        # Return default values
        return {
            "accuracy": 0.95,
            "precision": 0.92,
            "recall": 0.88,
            "f1_score": 0.90,
            "prediction_time_ms": 5.2,
            "throughput": 192.3
        }

def get_attack_statistics() -> Dict[str, Any]:
    """Get DDoS attack statistics"""
    try:
        # Calculate detection rate
        if ddos_statistics['total_detections'] > 0:
            ddos_statistics['detection_rate'] = (
                ddos_statistics['ddos_attacks'] / ddos_statistics['total_detections'] * 100
            )
        else:
            ddos_statistics['detection_rate'] = 0.0
        
        # Add some sample data if empty
        if not ddos_statistics['attack_types']:
            ddos_statistics['attack_types'] = {
                'TCP SYN Flood': 0,
                'UDP Flood': 0,
                'HTTP Flood': 0,
                'ICMP Flood': 0,
                'DNS Amplification': 0
            }
        
        return ddos_statistics
    except Exception as e:
        logger.error(f"Error getting attack statistics: {e}")
        return {
            "total_detections": 0,
            "ddos_attacks": 0,
            "false_positives": 0,
            "detection_rate": 0.0,
            "attack_types": {},
            "top_source_ips": {}
        }

def update_ddos_statistics(attack_data: Dict[str, Any]):
    """Update DDoS statistics with new attack data"""
    try:
        ddos_statistics['total_detections'] += 1
        
        if attack_data.get('is_ddos', False):
            ddos_statistics['ddos_attacks'] += 1
            
            # Update attack types
            attack_type = attack_data.get('attack_type', 'Unknown')
            if attack_type not in ddos_statistics['attack_types']:
                ddos_statistics['attack_types'][attack_type] = 0
            ddos_statistics['attack_types'][attack_type] += 1
            
            # Update top source IPs
            source_ip = attack_data.get('source_ip', 'unknown')
            if source_ip != 'unknown':
                if source_ip not in ddos_statistics['top_source_ips']:
                    ddos_statistics['top_source_ips'][source_ip] = 0
                ddos_statistics['top_source_ips'][source_ip] += 1
        else:
            ddos_statistics['false_positives'] += 1
        
        # Calculate detection rate
        if ddos_statistics['total_detections'] > 0:
            ddos_statistics['detection_rate'] = (
                ddos_statistics['ddos_attacks'] / ddos_statistics['total_detections'] * 100
            )
        
    except Exception as e:
        logger.error(f"Error updating DDoS statistics: {e}")

# ============================================================================
# Discord Integration
# ============================================================================

def send_discord_alert(message: str, severity: str = "info", embed_data: Dict[str, Any] = None, alert_type: str = "general", skip_deduplication: bool = False):
    """Send alert to Discord with optional detailed embed data
    
    Args:
        message: Alert message text
        severity: Alert severity (info, success, warning, error, critical)
        embed_data: Optional detailed embed data
        alert_type: Type of alert for deduplication (default: "general")
        skip_deduplication: If True, skip deduplication check (for critical alerts that need to be sent)
    """
    if not CONFIG["discord_webhook"]:
        logger.warning("Discord webhook not configured. Notification not sent.")
        return False
    
    # Global deduplication check (5 minutes for general alerts)
    if not skip_deduplication:
        global _alert_deduplication_cache
        current_time = datetime.now()
        
        # Create message hash for deduplication
        message_content = message
        if embed_data:
            # Use title and description from embed_data for hashing
            message_content = str(embed_data.get("title", "")) + str(embed_data.get("description", ""))
        
        message_hash = hashlib.md5(message_content.encode()).hexdigest()[:16]
        cache_key = (message_hash, alert_type)
        
        # Check if we've sent this alert recently
        if cache_key in _alert_deduplication_cache:
            last_sent_time = _alert_deduplication_cache[cache_key]
            time_since_last = (current_time - last_sent_time).total_seconds() / 60  # in minutes
            
            # Rate limit: 5 minutes for general alerts
            if time_since_last < 5:
                logger.debug(f"Discord alert suppressed (duplicate within {time_since_last:.1f} minutes): {message[:50]}...")
                return False
        
        # Clean up old entries (older than 1 hour) to prevent memory growth
        cutoff_time = current_time - timedelta(hours=1)
        _alert_deduplication_cache = {
            k: v for k, v in _alert_deduplication_cache.items()
            if v > cutoff_time
        }
        
        # Record this alert
        _alert_deduplication_cache[cache_key] = current_time
    
    try:
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        color_map = {
            "info": 3447003,      # Blue
            "success": 3066993,   # Green
            "warning": 16776960,  # Yellow
            "error": 15158332,    # Red
            "critical": 10038562  # Dark Red
        }
        
        # Build embed
        embed = {
            "title": f"{emoji_map.get(severity, 'ℹ️')} Healing Bot Alert",
            "color": color_map.get(severity, 3447003),
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Healing Bot Dashboard",
                "icon_url": "https://cdn.discordapp.com/emojis/🛡️.png"
            }
        }
        
        # If detailed embed data is provided, use it
        if embed_data:
            # Copy all embed_data fields to embed (title, description, fields, etc.)
            for key in ["title", "description", "fields", "thumbnail", "footer", "url", "timestamp", "color"]:
                if key in embed_data:
                    embed[key] = embed_data[key]
        else:
            # Simple message format
            embed["description"] = message
        
        payload = {
            "embeds": [embed]
        }
        
        # Send request with proper headers and response checking
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            CONFIG["discord_webhook"], 
            json=payload, 
            headers=headers,
            timeout=10
        )
        
        # Check response status
        if response.status_code == 204:
            logger.debug(f"Discord notification sent successfully (severity: {severity})")
            return True
        elif response.status_code in [200, 201]:
            logger.debug(f"Discord notification sent successfully (severity: {severity})")
            return True
        else:
            error_msg = f"Discord webhook returned status {response.status_code}"
            try:
                error_body = response.text
                if error_body:
                    error_msg += f": {error_body[:200]}"
            except:
                pass
            logger.error(f"Failed to send Discord alert: {error_msg}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Discord webhook request timed out after 10 seconds")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Discord webhook connection error: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord webhook request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending Discord alert: {e}", exc_info=True)
        return False

def send_early_warnings_discord_notification(warnings: List[Dict[str, Any]], warning_count: int, metrics: Dict[str, Any] = None):
    """Send Discord notification for early warnings"""
    if not CONFIG["discord_webhook"]:
        return False
    
    try:
        # Build warning list text
        warning_texts = []
        high_severity_count = 0
        medium_severity_count = 0
        
        for warning in warnings:
            severity = warning.get('severity', 'medium')
            message = warning.get('message', 'Unknown warning')
            wtype = warning.get('type', 'unknown')
            
            emoji = "🔴" if severity == 'high' else "🟡"
            warning_texts.append(f"{emoji} **{wtype.replace('_', ' ').title()}**: {message}")
            
            if severity == 'high':
                high_severity_count += 1
            elif severity == 'medium':
                medium_severity_count += 1
        
        # Determine notification severity
        if high_severity_count > 0:
            notif_severity = "critical" if high_severity_count >= 3 else "error"
        elif medium_severity_count > 0:
            notif_severity = "warning"
        else:
            notif_severity = "info"
        
        # Get system metrics if provided
        cpu = metrics.get('cpu_percent', metrics.get('cpu', 0)) if metrics else 0
        memory = metrics.get('memory_percent', metrics.get('memory', 0)) if metrics else 0
        disk = metrics.get('disk_percent', metrics.get('disk', 0)) if metrics else 0
        
        # Build embed
        fields = [
            {
                "name": "⚠️ Active Warnings",
                "value": f"**Total:** {warning_count}\n**High Severity:** {high_severity_count}\n**Medium Severity:** {medium_severity_count}",
                "inline": True
            },
            {
                "name": "💻 System Metrics",
                "value": f"**CPU:** {cpu:.1f}%\n**Memory:** {memory:.1f}%\n**Disk:** {disk:.1f}%",
                "inline": True
            }
        ]
        
        # Add warning details (limit to 10 most important)
        warning_details = "\n".join(warning_texts[:10])
        if len(warnings) > 10:
            warning_details += f"\n... and {len(warnings) - 10} more warning(s)"
        
        fields.append({
            "name": "📋 Warning Details",
            "value": warning_details[:1024],  # Discord field limit
            "inline": False
        })
        
        # Get dashboard URL
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:5001")
        dashboard_link = f"{dashboard_url}/static/healing-dashboard.html#predictive"
        
        embed_data = {
            "title": f"⚠️ Early Warning Indicators Detected ({warning_count} Active)",
            "description": f"**{warning_count}** early warning{'s' if warning_count != 1 else ''} detected by predictive maintenance system.",
            "color": 15158332 if high_severity_count > 0 else 16776960,  # Red if high severity, yellow otherwise
            "fields": fields,
            "footer": {
                "text": f"Healing Bot Dashboard • {dashboard_url}",
            },
            "timestamp": datetime.utcnow().isoformat(),
            "url": dashboard_link
        }
        
        success = send_discord_alert("", notif_severity, embed_data)
        if success:
            logger.info(f"Discord notification sent for {warning_count} early warnings")
        return success
        
    except Exception as e:
        logger.error(f"Error sending early warnings Discord notification: {e}", exc_info=True)
        return False

def send_time_to_failure_discord_notification(hours_until_failure: float, predicted_time: str = None, risk_percentage: float = None, metrics: Dict[str, Any] = None):
    """Send Discord notification for time-to-failure prediction"""
    if not CONFIG["discord_webhook"]:
        return False
    
    try:
        # Determine severity based on hours until failure
        if hours_until_failure < 1:
            severity = "critical"
            emoji = "🚨"
            urgency = "IMMEDIATE ACTION REQUIRED"
            color = 10038562  # Dark red
        elif hours_until_failure < 6:
            severity = "error"
            emoji = "🔴"
            urgency = "URGENT"
            color = 15158332  # Red
        elif hours_until_failure < 24:
            severity = "warning"
            emoji = "🟠"
            urgency = "HIGH PRIORITY"
            color = 16753920  # Orange
        else:
            severity = "warning"
            emoji = "🟡"
            urgency = "MONITORING"
            color = 16776960  # Yellow
        
        # Format predicted time
        predicted_time_str = "N/A"
        if predicted_time:
            try:
                dt = datetime.fromisoformat(predicted_time.replace('Z', '+00:00'))
                predicted_time_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                predicted_time_str = predicted_time
        
        # Format hours
        if hours_until_failure < 1:
            time_str = f"{hours_until_failure * 60:.1f} minutes"
        elif hours_until_failure < 24:
            time_str = f"{hours_until_failure:.1f} hours"
        else:
            days = hours_until_failure / 24
            time_str = f"{days:.1f} days ({hours_until_failure:.1f} hours)"
        
        # Get system metrics if provided
        cpu = metrics.get('cpu_percent', metrics.get('cpu', 0)) if metrics else 0
        memory = metrics.get('memory_percent', metrics.get('memory', 0)) if metrics else 0
        disk = metrics.get('disk_percent', metrics.get('disk', 0)) if metrics else 0
        
        # Build embed
        fields = [
            {
                "name": f"{emoji} Time to Failure",
                "value": f"**Estimated:** {time_str}\n**Predicted Time:** {predicted_time_str}\n**Urgency:** {urgency}",
                "inline": False
            }
        ]
        
        if risk_percentage is not None:
            fields.append({
                "name": "📊 Risk Assessment",
                "value": f"**Risk Score:** {risk_percentage:.1f}%\n**Level:** {'High' if risk_percentage > 70 else 'Medium' if risk_percentage > 50 else 'Low'}",
                "inline": True
            })
        
        fields.append({
            "name": "💻 System Metrics",
            "value": f"**CPU:** {cpu:.1f}%\n**Memory:** {memory:.1f}%\n**Disk:** {disk:.1f}%",
            "inline": True
        })
        
        # Add recommended actions
        recommendations = []
        if hours_until_failure < 6:
            recommendations.append("🔴 **Immediate action required** - System failure predicted soon")
            recommendations.append("📋 **Review system logs** - Check for error patterns")
            recommendations.append("🔄 **Consider preventive measures** - Restart services if needed")
        else:
            recommendations.append("📋 **Monitor system closely** - Watch for warning indicators")
            recommendations.append("🔍 **Review metrics** - Check dashboard for details")
        
        if recommendations:
            fields.append({
                "name": "💡 Recommended Actions",
                "value": "\n".join(recommendations),
                "inline": False
            })
        
        # Get dashboard URL
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:5001")
        dashboard_link = f"{dashboard_url}/static/healing-dashboard.html#predictive"
        
        embed_data = {
            "title": f"{emoji} Predictive Failure Detection - {time_str} Until Failure",
            "description": f"Predictive maintenance model estimates system failure in **{time_str}**.",
            "color": color,
            "fields": fields,
            "footer": {
                "text": f"Healing Bot Dashboard • {dashboard_url}",
            },
            "timestamp": datetime.utcnow().isoformat(),
            "url": dashboard_link
        }
        
        success = send_discord_alert("", severity, embed_data)
        if success:
            logger.info(f"Discord notification sent for time-to-failure: {hours_until_failure:.1f} hours")
        return success
        
    except Exception as e:
        logger.error(f"Error sending time-to-failure Discord notification: {e}", exc_info=True)
        return False

def send_detailed_critical_alert(issue: Dict[str, Any], system_metrics: Dict[str, Any] = None):
    """Send detailed Discord alert for critical errors"""
    if not CONFIG["discord_webhook"]:
        logger.warning("Discord webhook not configured. Critical alert not sent.")
        return False
    
    try:
        # Get issue details
        service_name = issue.get('service', 'Unknown Service')
        error_message = issue.get('message', 'No message available')
        error_level = issue.get('level', 'CRITICAL')
        error_category = issue.get('category', 'CRITICAL')
        priority = issue.get('priority', 2)
        timestamp = issue.get('timestamp', datetime.now().isoformat())
        source = issue.get('source', 'unknown')
        source_file = issue.get('source_file', issue.get('tag', 'unknown'))
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            relative_time = dt.strftime('%H:%M:%S')
        except:
            formatted_time = timestamp
            relative_time = "Unknown"
        
        # Get system metrics if not provided
        if system_metrics is None:
            try:
                system_metrics = get_system_metrics()
            except:
                system_metrics = {
                    'cpu': 0,
                    'memory': 0,
                    'disk': 0
                }
        
        # Get hostname for multi-server identification
        try:
            hostname = os.uname().nodename
        except:
            hostname = "unknown"
        
        # Determine priority description
        priority_desc = {
            0: "Emergency - System unusable",
            1: "Alert - Immediate action required",
            2: "Critical - Critical condition",
            3: "Error - Error condition",
            4: "Warning - Warning condition"
        }.get(priority, f"Priority {priority}")
        
        # Determine impact level
        impact_level = "🔴 CRITICAL" if priority <= 2 else "🟠 HIGH" if priority == 3 else "🟡 MEDIUM"
        
        # Get service status
        service_status = "❓ Unknown"
        try:
            monitor = get_critical_services_monitor()
            if monitor:
                status = monitor.service_status.get(service_name, {})
                if status.get('active', False):
                    service_status = "✅ Active"
                else:
                    service_status = "❌ Inactive"
        except:
            pass
        
        # Analyze error message for key information
        error_lower = error_message.lower()
        error_type = "Unknown Error"
        if any(kw in error_lower for kw in ['crash', 'abort', 'terminated', 'killed']):
            error_type = "💀 Service Crash"
        elif any(kw in error_lower for kw in ['timeout', 'timed out']):
            error_type = "⏱️ Timeout"
        elif any(kw in error_lower for kw in ['connection', 'connect', 'refused']):
            error_type = "🔌 Connection Error"
        elif any(kw in error_lower for kw in ['permission', 'denied', 'unauthorized']):
            error_type = "🔐 Permission Error"
        elif any(kw in error_lower for kw in ['memory', 'oom', 'out of memory']):
            error_type = "💾 Memory Error"
        elif any(kw in error_lower for kw in ['disk', 'space', 'full', 'no space']):
            error_type = "💿 Disk Space Error"
        elif any(kw in error_lower for kw in ['failed', 'failure', 'fail']):
            error_type = "❌ Operation Failed"
        
        # Truncate long messages
        display_message = error_message
        if len(display_message) > 1000:
            display_message = display_message[:1000] + "\n... (truncated)"
        
        # Determine CPU/Memory/Disk status with emojis
        cpu = system_metrics.get('cpu', 0)
        memory = system_metrics.get('memory', 0)
        disk = system_metrics.get('disk', 0)
        
        cpu_status = "🟢 Normal" if cpu < 80 else "🟡 High" if cpu < 95 else "🔴 Critical"
        memory_status = "🟢 Normal" if memory < 80 else "🟡 High" if memory < 95 else "🔴 Critical"
        disk_status = "🟢 Normal" if disk < 80 else "🟡 High" if disk < 95 else "🔴 Critical"
        
        # Build Discord embed with fields
        fields = [
            {
                "name": "🔴 Service Information",
                "value": f"**Service:** `{service_name}`\n**Status:** {service_status}\n**Category:** `{error_category}`\n**Source:** `{source}`\n**Host:** `{hostname}`",
                "inline": True
            },
            {
                "name": "📊 Error Details",
                "value": f"**Type:** {error_type}\n**Level:** `{error_level}`\n**Priority:** `{priority}` ({priority_desc})\n**Impact:** {impact_level}",
                "inline": True
            },
            {
                "name": "⏰ Timing & Location",
                "value": f"**Detected:** {formatted_time}\n**Time:** {relative_time}\n**Source File:** `{source_file}`",
                "inline": True
            },
            {
                "name": "💻 System Resources",
                "value": f"**CPU:** {cpu:.1f}% {cpu_status}\n**Memory:** {memory:.1f}% {memory_status}\n**Disk:** {disk:.1f}% {disk_status}",
                "inline": True
            }
        ]
        
        # Add recommended actions based on error type
        recommendations = []
        if 'crash' in error_lower or 'abort' in error_lower:
            recommendations.append("🔄 **Restart the service** - Service may have crashed")
        if 'timeout' in error_lower:
            recommendations.append("⏱️ **Check service response time** - Service may be overloaded")
        if 'connection' in error_lower or 'refused' in error_lower:
            recommendations.append("🔌 **Check network connectivity** - Service may be unreachable")
        if 'permission' in error_lower or 'denied' in error_lower:
            recommendations.append("🔐 **Check file permissions** - Service may lack required permissions")
        if 'memory' in error_lower or 'oom' in error_lower:
            recommendations.append("💾 **Check memory usage** - System may be out of memory")
        if 'disk' in error_lower or 'space' in error_lower:
            recommendations.append("💿 **Check disk space** - Disk may be full")
        if not recommendations:
            recommendations.append("📋 **Review logs** - Check dashboard for more details")
            recommendations.append("🔍 **Analyze with AI** - Use AI analysis feature in dashboard")
        
        if recommendations:
            fields.append({
                "name": "💡 Recommended Actions",
                "value": "\n".join(recommendations),
                "inline": False
            })
        
        # Get dashboard URL from config or use default
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:5001")
        dashboard_link = f"{dashboard_url}/static/healing-dashboard.html#logs"
        
        # Build embed
        embed_data = {
            "title": f"🚨 CRITICAL ERROR DETECTED - {service_name}",
            "description": f"```\n{display_message}\n```",
            "color": 10038562,  # Dark red for critical
            "fields": fields,
            "footer": {
                "text": f"Healing Bot Dashboard • {dashboard_url}",
            },
            "timestamp": timestamp,
            "url": dashboard_link
        }
        
        success = send_discord_alert("", "critical", embed_data)
        if success:
            logger.info(f"Detailed Discord notification sent for CRITICAL error: {service_name}")
        else:
            logger.warning(f"Failed to send detailed Discord notification for CRITICAL error: {service_name}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending detailed Discord alert: {e}", exc_info=True)
        # Fallback to simple alert
        try:
            service_name = issue.get('service', 'Unknown Service')
            error_message = issue.get('message', 'No message')[:500]
            return send_discord_alert(f"🚨 CRITICAL ERROR: {service_name}\n\n{error_message}", "critical")
        except:
            return False

# ============================================================================
# AI Log Analysis (TF-IDF)
# ============================================================================

def analyze_logs_tfidf(logs: List[str]) -> Dict[str, Any]:
    """Analyze logs using TF-IDF for keyword extraction"""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        if not logs:
            return {"keywords": [], "anomalies": []}
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(max_features=20, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(logs)
        
        # Get feature names (keywords)
        keywords = vectorizer.get_feature_names_out()
        
        # Calculate importance scores
        importance = tfidf_matrix.sum(axis=0).A1
        keyword_scores = dict(zip(keywords, importance))
        
        # Sort by importance
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Detect anomalies (error keywords)
        error_keywords = ['error', 'fail', 'exception', 'critical', 'warning']
        anomalies = [kw for kw, score in sorted_keywords if any(ek in kw.lower() for ek in error_keywords)]
        
        return {
            "keywords": [{"word": kw, "score": float(score)} for kw, score in sorted_keywords[:10]],
            "anomalies": anomalies
        }
    except Exception as e:
        logger.error(f"Error in TF-IDF analysis: {e}")
        return {"keywords": [], "anomalies": []}

# ============================================================================
# Event Logging
# ============================================================================

def log_event(level: str, message: str):
    """Log an event to the buffer"""
    log_buffer.append({
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 1000 logs
    if len(log_buffer) > 1000:
        log_buffer.pop(0)

# ============================================================================
# Background Tasks
# ============================================================================

async def monitoring_loop():
    """Main monitoring loop"""
    loop_counter = 0
    while True:
        try:
            # Get system metrics
            metrics = get_system_metrics()
            
            # Check services
            if CONFIG["auto_restart"]:
                services = get_all_services_status()
                stopped_services = [s for s in services if not s.get("active", False)]
                if stopped_services:
                    logger.info(f"🔍 Monitoring loop detected {len(stopped_services)} stopped service(s): {[s['name'] for s in stopped_services]}")
                    for service in stopped_services:
                        service_name = service["name"]
                        service_status = service.get("status", "unknown")
                        logger.info(f"🔄 Auto-restarting service: {service_name} (status: {service_status})")
                        restart_service(service_name)
            
            # Check resource hogs
            auto_detect_resource_hogs()
            
            # Cleanup old notification history entries (every 100 iterations = ~3.3 minutes)
            if loop_counter % 100 == 0:
                try:
                    notification_manager.cleanup_old_entries()
                except Exception as e:
                    logger.error(f"Error cleaning up notification history: {e}")
            
            # Check disk usage (only run cleanup once per hour)
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > CONFIG["disk_threshold"]:
                # Check if cleanup was run in the last hour
                if last_cleanup_time is None:
                    # Never run before, run it
                    run_disk_cleanup()
                else:
                    time_since_last_cleanup = (datetime.now() - last_cleanup_time).total_seconds()
                    if time_since_last_cleanup >= 3600:  # 1 hour = 3600 seconds
                        # More than an hour has passed, safe to run cleanup
                        run_disk_cleanup()
                    # Otherwise, skip (cleanup already ran in the last hour)
            
            # Fetch ML metrics every 5 iterations (10 seconds)
            if loop_counter % 5 == 0:
                try:
                    fetch_ml_metrics()
                except Exception as e:
                    logger.error(f"Error fetching ML metrics: {e}")
            
            loop_counter += 1
            
            # Broadcast to connected clients
            await manager.broadcast(metrics)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        await asyncio.sleep(2)  # Update every 2 seconds

# ============================================================================
# API Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start background tasks and initialize cloud components"""
    try:
        # Start monitoring loop (non-blocking)
        asyncio.create_task(monitoring_loop())
        logger.info("✅ Monitoring loop started")
        
        # Initialize cloud simulation components in background (don't block startup)
        async def init_cloud_components_async():
            try:
                # Run synchronous function in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, initialize_cloud_components)
                logger.info("✅ Cloud components initialized")
            except Exception as e:
                logger.error(f"⚠️  Error initializing cloud components (service will continue): {e}", exc_info=True)
        
        # Start cloud components initialization in background
        asyncio.create_task(init_cloud_components_async())
        
    except Exception as e:
        logger.error(f"⚠️  Error during startup (service will continue): {e}", exc_info=True)
        # Don't fail startup if initialization fails
    
    # Initialize with some sample DDoS data if empty
    if ddos_statistics['total_detections'] == 0:
        # Add sample statistics for demo purposes
        ddos_statistics['total_detections'] = 127
        ddos_statistics['ddos_attacks'] = 23
        ddos_statistics['false_positives'] = 5
        ddos_statistics['detection_rate'] = 18.1
        ddos_statistics['attack_types'] = {
            'TCP SYN Flood': 8,
            'UDP Flood': 6,
            'HTTP Flood': 5,
            'ICMP Flood': 3,
            'DNS Amplification': 1
        }
        ddos_statistics['top_source_ips'] = {
            '192.168.1.100': 12,
            '10.0.0.45': 8,
            '172.16.0.23': 5,
            '203.0.113.42': 3,
            '198.51.100.88': 2
        }
    
    # Initialize ML performance history with sample data
    if not ml_performance_history['timestamps']:
        base_time = datetime.now() - timedelta(minutes=20)
        
        for i in range(20):
            timestamp = base_time + timedelta(minutes=i)
            ml_performance_history['timestamps'].append(timestamp.isoformat())
            ml_performance_history['accuracy'].append(0.93 + random.uniform(-0.02, 0.02))
            ml_performance_history['precision'].append(0.91 + random.uniform(-0.02, 0.02))
            ml_performance_history['recall'].append(0.87 + random.uniform(-0.02, 0.02))
            ml_performance_history['f1_score'].append(0.89 + random.uniform(-0.02, 0.02))
            ml_performance_history['prediction_times'].append(4.5 + random.uniform(-1.0, 1.5))
    
    logger.info("Healing Bot Dashboard API started")

@app.get("/")
async def root():
    """Serve the dashboard"""
    try:
        dashboard_path = Path(__file__).parent.parent / "dashboard" / "static" / "healing-dashboard.html"
        if dashboard_path.exists():
            with open(dashboard_path, "r") as f:
                return HTMLResponse(content=f.read())
        else:
            # Return a simple HTML page if dashboard file not found
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head><title>Healing Dashboard API</title></head>
            <body>
                <h1>Healing Dashboard API</h1>
                <p>API is running. Use <a href="/api/health">/api/health</a> for health checks.</p>
                <p>Available endpoints: <a href="/api/metrics">/api/metrics</a>, <a href="/api/services">/api/services</a></p>
            </body>
            </html>
            """)
    except Exception as e:
        logger.error(f"Error serving dashboard: {e}")
        return HTMLResponse(content=f"<h1>Healing Dashboard API</h1><p>Error: {str(e)}</p>", status_code=500)

@app.websocket("/ws/healing")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics")
async def get_metrics():
    """Get current system metrics"""
    return get_system_metrics()

@app.get("/api/services")
async def get_services():
    """Get all services status (all services - running and stopped)"""
    all_services = get_all_services_status()
    # Return all services (both running and stopped) for full management
    return {"services": all_services}

@app.post("/api/services/{service_name}/start")
async def start_service_endpoint(service_name: str):
    """Start a specific service"""
    try:
        success = start_service(service_name)
        return {"success": success, "service": service_name}
    except Exception as e:
        logger.error(f"Error starting service {service_name}: {e}")
        return {"success": False, "service": service_name, "error": str(e)}

@app.post("/api/services/{service_name}/stop")
async def stop_service_endpoint(service_name: str):
    """Stop a specific service"""
    try:
        success = stop_service(service_name)
        return {"success": success, "service": service_name}
    except Exception as e:
        logger.error(f"Error stopping service {service_name}: {e}")
        return {"success": False, "service": service_name, "error": str(e)}

@app.post("/api/services/{service_name}/restart")
async def restart_service_endpoint(service_name: str):
    """Restart a specific service"""
    try:
        success = restart_service(service_name)
        return {"success": success, "service": service_name}
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {e}")
        return {"success": False, "service": service_name, "error": str(e)}

@app.get("/api/processes/top")
async def get_top_processes_endpoint(limit: int = 10):
    """Get top processes"""
    return get_top_processes(limit)

@app.post("/api/processes/kill")
async def kill_process_endpoint(data: dict):
    """Kill a process by PID"""
    pid = data.get("pid")
    if not pid:
        raise HTTPException(status_code=400, detail="PID is required")
    
    success = kill_resource_hog(pid)
    return {"success": success, "pid": pid}

@app.get("/api/ssh/attempts")
async def get_ssh_attempts():
    """Get SSH intrusion attempts"""
    return {"attempts": parse_ssh_logs()}

@app.post("/api/ssh/block")
async def block_ip_endpoint(data: dict):
    """Block an IP address"""
    ip = data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="IP is required")
    
    block_ip(ip)
    return {"success": True, "ip": ip}

@app.post("/api/ssh/unblock")
async def unblock_ip_endpoint(data: dict):
    """Unblock an IP address"""
    ip = data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="IP is required")
    
    unblock_ip(ip)
    return {"success": True, "ip": ip}

@app.get("/api/disk/status")
async def get_disk_status():
    """Get disk usage status"""
    disk = psutil.disk_usage('/')
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
        "last_cleanup": last_cleanup_time.isoformat() if last_cleanup_time else None,
        "last_freed_space": last_freed_space
    }

@app.post("/api/disk/cleanup")
async def cleanup_disk_endpoint():
    """Run disk cleanup"""
    result = run_disk_cleanup()
    return result

@app.post("/api/discord/test")
async def test_discord_endpoint(data: dict):
    """Test Discord webhook"""
    webhook = data.get("webhook")
    if webhook:
        webhook = webhook.strip()
        # Remove quotes if present
        if webhook.startswith('"') and webhook.endswith('"'):
            webhook = webhook[1:-1]
        if webhook.startswith("'") and webhook.endswith("'"):
            webhook = webhook[1:-1]
        CONFIG["discord_webhook"] = webhook
    
    if not CONFIG["discord_webhook"]:
        return {"success": False, "error": "Discord webhook not configured"}
    
    success = send_discord_alert("Test notification from Healing Bot Dashboard", "info")
    if success:
        return {"success": True, "message": "Test notification sent successfully"}
    else:
        return {"success": False, "error": "Failed to send test notification. Check server logs for details."}

@app.get("/api/discord/status")
async def get_discord_status():
    """Get Discord webhook configuration status"""
    webhook = CONFIG.get("discord_webhook", "")
    is_configured = bool(webhook)
    
    # Check if webhook is in environment (check both variable names)
    env_webhook = os.getenv("DISCORD_WEBHOOK") or os.getenv("DISCORD_WEBHOOK_URL", "")
    env_webhook = env_webhook.strip() if env_webhook else ""
    if env_webhook.startswith('"') and env_webhook.endswith('"'):
        env_webhook = env_webhook[1:-1]
    if env_webhook.startswith("'") and env_webhook.endswith("'"):
        env_webhook = env_webhook[1:-1]
    
    return {
        "configured": is_configured,
        "has_env_var": bool(env_webhook),
        "webhook_length": len(webhook) if webhook else 0,
        "env_file_path": str(env_path_abs),
        "env_file_exists": env_path_abs.exists()
    }

@app.post("/api/discord/configure")
async def configure_discord(data: dict):
    """Configure Discord webhook"""
    webhook = data.get("webhook", "").strip()
    # Remove quotes if present
    if webhook.startswith('"') and webhook.endswith('"'):
        webhook = webhook[1:-1]
    if webhook.startswith("'") and webhook.endswith("'"):
        webhook = webhook[1:-1]
    
    CONFIG["discord_webhook"] = webhook
    
    if webhook:
        # Mask the webhook URL for security
        webhook_display = webhook
        if len(webhook_display) > 50:
            webhook_display = webhook_display[:30] + "..." + webhook_display[-20:]
        logger.info(f"Discord webhook configured: {webhook_display}")
    else:
        logger.info("Discord webhook cleared")
    
    return {"success": True, "message": "Discord webhook configured" if webhook else "Discord webhook cleared"}

@app.post("/api/discord/reload")
async def reload_discord_config():
    """Reload Discord webhook from environment variables"""
    # Reload .env file
    load_dotenv(dotenv_path=str(env_path_abs), override=True)
    
    # Reload config
    new_config = load_config()
    old_webhook = CONFIG.get("discord_webhook", "")
    CONFIG["discord_webhook"] = new_config["discord_webhook"]
    
    if CONFIG["discord_webhook"]:
        webhook_display = CONFIG["discord_webhook"]
        if len(webhook_display) > 50:
            webhook_display = webhook_display[:30] + "..." + webhook_display[-20:]
        logger.info(f"Discord webhook reloaded from .env: {webhook_display}")
        return {
            "success": True, 
            "message": "Discord webhook reloaded from .env file",
            "was_configured": bool(old_webhook),
            "now_configured": True
        }
    else:
        logger.warning("Discord webhook not found in .env file after reload")
        return {
            "success": False,
            "message": "DISCORD_WEBHOOK not found in .env file",
            "was_configured": bool(old_webhook),
            "now_configured": False
        }

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    """Get recent logs"""
    return {"logs": log_buffer[-limit:]}

@app.post("/api/logs/analyze")
async def analyze_logs_endpoint(data: dict):
    """Analyze logs with AI (TF-IDF)"""
    query = data.get("query", "")
    logs = [log["message"] for log in log_buffer]
    
    analysis = analyze_logs_tfidf(logs)
    
    # Simple explanation based on query
    explanation = f"Analysis of {len(logs)} log entries:\n"
    explanation += f"Top keywords: {', '.join([kw['word'] for kw in analysis['keywords'][:5]])}\n"
    
    if analysis['anomalies']:
        explanation += f"⚠️ Anomalies detected: {', '.join(analysis['anomalies'])}"
    else:
        explanation += "✅ No anomalies detected"
    
    return {"explanation": explanation, "analysis": analysis}

# System Logs Endpoints
@app.get("/api/system-logs/recent")
async def get_system_logs(limit: int = 100, level: str = None, source: str = None):
    """Get recent system-wide logs"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return {
                "status": "error",
                "message": "System log collector not initialized",
                "logs": []
            }
        
        logs = collector.get_recent_logs(limit=limit, level=level, source=source)
        
        return {
            "status": "success",
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        return {
            "status": "error",
            "message": str(e),
            "logs": []
        }

@app.get("/api/system-logs/statistics")
async def get_system_log_statistics():
    """Get statistics about system-wide logs"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return {
                "status": "error",
                "message": "System log collector not initialized"
            }
        
        stats = collector.get_log_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting system log statistics: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/system-logs/sources")
async def get_system_log_sources():
    """Get available system log sources"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return {
                "status": "error",
                "message": "System log collector not initialized"
            }
        
        sources = []
        for source_name, config in collector.log_sources.items():
            sources.append({
                "name": source_name,
                "enabled": config["enabled"],
                "description": f"{source_name.capitalize()} logs"
            })
        
        return {
            "status": "success",
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Error getting system log sources: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Centralized Logs Endpoints
@app.get("/api/central-logs/recent")
async def get_central_recent_logs(limit: int = 100):
    """Get recent centralized logs"""
    try:
        # Use the global centralized_logger from the module
        from centralized_logger import centralized_logger as _centralized_logger
        if not _centralized_logger:
            return {
                "status": "error",
                "message": "Centralized logging not initialized",
                "logs": []
            }
        
        logs = _centralized_logger.get_recent_logs(limit=limit)
        
        return {
            "status": "success",
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting centralized logs: {e}")
        return {
            "status": "error",
            "message": str(e),
            "logs": []
        }

@app.get("/api/central-logs/statistics")
async def get_central_log_statistics():
    """Get centralized logging statistics"""
    try:
        # Use the global centralized_logger from the module
        from centralized_logger import centralized_logger as _centralized_logger
        if not _centralized_logger:
            return {
                "status": "error",
                "message": "Centralized logging not initialized"
            }
        
        stats = _centralized_logger.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting centralized log statistics: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/central-logs/services")
async def get_monitored_services():
    """Get list of all monitored services"""
    try:
        # Use the global centralized_logger from the module
        from centralized_logger import centralized_logger as _centralized_logger
        if not _centralized_logger:
            return {
                "status": "error",
                "message": "Centralized logging not initialized",
                "services": []
            }
        
        services = _centralized_logger.get_service_list()
        
        return {
            "status": "success",
            "services": services,
            "count": len(services)
        }
    except Exception as e:
        logger.error(f"Error getting monitored services: {e}")
        return {
            "status": "error",
            "message": str(e),
            "services": []
        }

# Fluent Bit Log Endpoints
@app.get("/api/fluent-bit/recent")
async def get_fluent_bit_recent_logs(limit: int = 100, service: str = None, level: str = None, tag: str = None):
    """Get recent logs from Fluent Bit"""
    try:
        # Import with reload to get fresh module state
        import fluent_bit_reader
        import importlib
        importlib.reload(fluent_bit_reader)
        
        reader = fluent_bit_reader.fluent_bit_reader
        
        # If reader doesn't exist or has no logs, try to initialize/find it
        if not reader or (hasattr(reader, 'log_cache') and len(reader.log_cache) == 0):
            # Try to find log file in multiple locations
            project_root = Path(__file__).parent.parent.parent
            possible_paths = [
                '/home/cdrditgis/Documents/Healing-bot/logs/fluent-bit/fluent-bit-output.jsonl',
                str(project_root / 'logs' / 'fluent-bit' / 'fluent-bit-output.jsonl'),
                str(Path.home() / 'Documents' / 'Healing-bot' / 'logs' / 'fluent-bit' / 'fluent-bit-output.jsonl'),
                os.getenv('FLUENT_BIT_LOG_PATH', ''),
                '/var/log/fluent-bit/fluent-bit-output.jsonl'
            ]
            
            log_path = None
            for path in possible_paths:
                if path:
                    # Convert to absolute path
                    abs_path = str(Path(path).absolute()) if not os.path.isabs(path) else path
                    if Path(abs_path).exists() and os.access(abs_path, os.R_OK):
                        log_path = abs_path
                        logger.info(f"Found Fluent Bit log file at: {log_path}")
                        break
            
            if not log_path:
                # Use default even if it doesn't exist yet
                default_rel = str(project_root / 'logs' / 'fluent-bit' / 'fluent-bit-output.jsonl')
                log_path = str(Path(default_rel).absolute())
                logger.info(f"Using default Fluent Bit log path: {log_path}")
            
            # Initialize or re-initialize the reader
            logger.info(f"Initializing Fluent Bit reader with: {log_path}")
            reader = fluent_bit_reader.initialize_fluent_bit_reader(log_path)
            if reader:
                # Force refresh to load existing logs
                reader.refresh_logs()
                logger.info(f"Fluent Bit reader loaded {len(reader.log_cache)} logs")
        
        if not reader:
            return {
                "status": "success",
                "message": "Fluent Bit reader could not be initialized. Check logs for details.",
                "logs": [],
                "count": 0
            }
        
        # Check if reader has logs
        if not hasattr(reader, 'log_cache') or len(reader.log_cache) == 0:
            # Try refreshing one more time
            try:
                reader.refresh_logs()
            except Exception as e:
                logger.debug(f"Error refreshing Fluent Bit logs: {e}")
            
            if len(reader.log_cache) == 0:
                # Check if Fluent Bit container is running
                import subprocess
                fluent_bit_running = False
                docker_available = False
                docker_error = None
                
                try:
                    result = subprocess.run(['docker', 'ps', '--filter', 'name=fluent-bit', '--format', '{{.Names}}'], 
                                          capture_output=True, text=True, timeout=5)
                    docker_available = True
                    fluent_bit_running = 'fluent-bit' in result.stdout
                except FileNotFoundError:
                    docker_error = "Docker is not installed"
                except PermissionError:
                    docker_error = "Permission denied - user needs to be in docker group or use sudo"
                except Exception as e:
                    docker_error = f"Docker check failed: {str(e)}"
                
                # Check if log file exists (even if empty, it means Fluent Bit was running)
                log_file_exists = reader.log_file_path.exists()
                
                if not docker_available or docker_error:
                    # Docker not available or permission denied
                    if log_file_exists:
                        return {
                            "status": "success",
                            "message": f"Fluent Bit log file exists but is empty. {docker_error if docker_error else 'Docker may not be accessible'}. Please ensure Fluent Bit container is running: sudo ./scripts/start-fluent-bit.sh",
                            "logs": [],
                            "count": 0,
                            "suggestion": "Switch to 'Centralized Logger' log source to view system logs without Docker."
                        }
                    else:
                        return {
                            "status": "success",
                            "message": f"Fluent Bit is not running. {docker_error if docker_error else 'Docker may not be accessible'}. To start Fluent Bit: sudo ./scripts/start-fluent-bit.sh (requires Docker). Alternatively, switch to 'Centralized Logger' log source.",
                            "logs": [],
                            "count": 0,
                            "suggestion": "Switch to 'Centralized Logger' log source in the dashboard to view system logs.",
                            "docker_error": docker_error
                        }
                elif not fluent_bit_running:
                    # Docker available but Fluent Bit not running
                    if log_file_exists:
                        return {
                            "status": "success",
                            "message": "Fluent Bit container is not running, but log file exists. Start Fluent Bit with: ./scripts/start-fluent-bit.sh",
                            "logs": [],
                            "count": 0,
                            "suggestion": "Switch to 'Centralized Logger' log source to view system logs."
                        }
                    else:
                        return {
                            "status": "success",
                            "message": "Fluent Bit container is not running. Please start it with: ./scripts/start-fluent-bit.sh",
                            "logs": [],
                            "count": 0,
                            "suggestion": "Switch to 'Centralized Logger' log source in the dashboard to view system logs."
                        }
                else:
                    # Fluent Bit is running but no logs yet
                    return {
                        "status": "success",
                        "message": "Fluent Bit is running but no logs available yet. Fluent Bit may still be starting (wait 10-30 seconds) or no logs have been processed. The log file will be created at: " + str(reader.log_file_path),
                        "logs": [],
                        "count": 0,
                        "log_file_path": str(reader.log_file_path),
                        "suggestion": "Wait a moment and refresh, or switch to 'Centralized Logger' to view system logs immediately."
                    }
        
        # Refresh logs to get latest
        try:
            reader.refresh_logs()
        except Exception as e:
            logger.debug(f"Error refreshing Fluent Bit logs: {e}")
        
        logs = reader.get_recent_logs(
            limit=limit,
            service=service,
            level=level,
            tag=tag
        )
        
        return {
            "status": "success",
            "logs": logs,
            "count": len(logs),
            "source": "fluent-bit"
        }
    except Exception as e:
        logger.error(f"Error getting Fluent Bit logs: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "logs": []
        }

@app.get("/api/fluent-bit/statistics")
async def get_fluent_bit_statistics():
    """Get Fluent Bit log statistics"""
    try:
        if not fluent_bit_reader:
            log_path = os.getenv('FLUENT_BIT_LOG_PATH', '/var/log/fluent-bit/fluent-bit-output.jsonl')
            initialize_fluent_bit_reader(log_path)
        
        if not fluent_bit_reader:
            return {
                "status": "error",
                "message": "Fluent Bit reader not initialized"
            }
        
        stats = fluent_bit_reader.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats,
            "source": "fluent-bit"
        }
    except Exception as e:
        logger.error(f"Error getting Fluent Bit statistics: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/fluent-bit/sources")
async def get_fluent_bit_sources():
    """Get list of available Fluent Bit log sources/tags"""
    try:
        if not fluent_bit_reader:
            log_path = os.getenv('FLUENT_BIT_LOG_PATH', '/var/log/fluent-bit/fluent-bit-output.jsonl')
            initialize_fluent_bit_reader(log_path)
        
        if not fluent_bit_reader:
            return {
                "status": "error",
                "message": "Fluent Bit reader not initialized",
                "sources": []
            }
        
        sources = fluent_bit_reader.get_sources()
        
        return {
            "status": "success",
            "sources": sources,
            "count": len(sources),
            "source": "fluent-bit"
        }
    except Exception as e:
        logger.error(f"Error getting Fluent Bit sources: {e}")
        return {
            "status": "error",
            "message": str(e),
            "sources": []
        }

# Critical Services Endpoints
@app.get("/api/critical-services/list")
async def get_critical_services_list():
    """Get list of all critical services by category"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return {
                "status": "error",
                "message": "Critical services monitor not initialized"
            }
        
        service_list = monitor.get_service_list()
        
        return {
            "status": "success",
            "services": service_list
        }
    except Exception as e:
        logger.error(f"Error getting critical services list: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/critical-services/logs")
async def get_critical_services_logs(limit: int = 100, level: str = None, category: str = None, service: str = None):
    """Get logs from critical services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return {
                "status": "error",
                "message": "Critical services monitor not initialized",
                "logs": []
            }
        
        # Get logs based on filters
        if category:
            logs = monitor.get_logs_by_category(category, limit=limit)
        elif service:
            logs = monitor.get_logs_by_service(service, limit=limit)
        else:
            logs = monitor.get_recent_logs(limit=limit, level=level)
        
        return {
            "status": "success",
            "logs": logs,
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting critical services logs: {e}")
        return {
            "status": "error",
            "message": str(e),
            "logs": []
        }

@app.get("/api/critical-services/issues")
async def get_critical_service_issues(include_test: bool = False):
    """Get critical issues from monitored services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return {
                "status": "error",
                "message": "Critical services monitor not initialized",
                "issues": [],
                "count": 0
            }
        
        # Run get_critical_issues with timeout to prevent hanging
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            issues = await asyncio.wait_for(
                loop.run_in_executor(None, monitor.get_critical_issues),
                timeout=3.0  # 3 second timeout - fast response
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout getting critical issues - returning empty result")
            issues = []
        except Exception as e:
            logger.error(f"Error in executor: {e}")
            issues = []
        
        # Add test issue if requested
        if include_test and len(issues) == 0:
            from datetime import datetime
            test_issue = {
                'timestamp': datetime.now().isoformat(),
                'service': 'test-critical-service',
                'category': 'CRITICAL',
                'level': 'CRITICAL',
                'severity': 'CRITICAL',
                'priority': 2,
                'message': 'TEST: This is a test CRITICAL error to verify the dashboard is working correctly.',
                'description': 'Test service - for verification purposes',
                'source': 'test'
            }
            issues.insert(0, test_issue)
        
        # Check for new CRITICAL errors and send Discord notifications
        new_critical_count = 0
        
        for issue in issues:
            # Only notify for CRITICAL severity issues
            severity = (issue.get('severity') or issue.get('level') or '').upper()
            priority = issue.get('priority', 6)
            
            if severity in ['CRITICAL', 'CRIT'] or priority <= 2:
                # Create stable unique identifier for this error (service + message hash, no timestamp)
                service = issue.get('service', 'unknown')
                message = issue.get('message', '')
                message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
                error_id = (service, message_hash)  # Stable identifier without timestamp
                
                current_time = datetime.now()
                should_notify = False
                
                # Check if we've seen this error before
                if error_id not in notified_critical_errors:
                    # New error - always notify
                    should_notify = True
                    notified_critical_errors.add(error_id)
                else:
                    # Error seen before - check rate limiting (30 minutes)
                    global _critical_error_notification_times
                    if error_id in _critical_error_notification_times:
                        time_since_last = (current_time - _critical_error_notification_times[error_id]).total_seconds() / 60
                        if time_since_last >= 30:
                            # 30+ minutes since last notification - notify again
                            should_notify = True
                        else:
                            logger.debug(f"Critical error notification suppressed for {service} (sent {time_since_last:.1f} minutes ago)")
                    else:
                        # Error in set but no timestamp recorded - notify to be safe
                        should_notify = True
                
                if should_notify:
                    new_critical_count += 1
                    
                    # Get system metrics for context
                    try:
                        system_metrics = get_system_metrics()
                    except:
                        system_metrics = None
                    
                    # Send detailed Discord notification
                    send_detailed_critical_alert(issue, system_metrics)
                    service_name = issue.get('service', 'Unknown Service')
                    error_message = issue.get('message', 'No message')
                    logger.info(f"Detailed Discord notification sent for new CRITICAL error: {service_name} - {error_message[:50]}")
                    
                    # Record notification time
                    global _critical_error_notification_times
                    _critical_error_notification_times[error_id] = current_time
                    
                    # Clean up old notification times (older than 2 hours)
                    cutoff_time = current_time - timedelta(hours=2)
                    _critical_error_notification_times = {
                        k: v for k, v in _critical_error_notification_times.items()
                        if v > cutoff_time
                    }
        
        # Clean up old notified errors (keep last 1000 to prevent memory growth)
        if len(notified_critical_errors) > 1000:
            # Keep only the most recent 500
            notified_critical_errors.clear()
            _critical_error_notification_times.clear()
            # Re-add current issues
            for issue in issues[:500]:
                service = issue.get('service', 'unknown')
                message = issue.get('message', '')
                message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
                error_id = (service, message_hash)  # Stable identifier
                notified_critical_errors.add(error_id)
        
        if new_critical_count > 0:
            logger.info(f"Sent Discord notifications for {new_critical_count} new CRITICAL error(s)")
        
        # Filter out ignored alerts
        filtered_issues = []
        for issue in issues:
            service = issue.get('service', 'unknown')
            message = issue.get('message', '')
            message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
            alert_id = (service, message_hash)  # Stable identifier
            
            if alert_id not in ignored_alerts:
                filtered_issues.append(issue)
        
        return {
            "status": "success",
            "issues": filtered_issues,
            "count": len(filtered_issues)
        }
    except Exception as e:
        logger.error(f"Error getting critical service issues: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "message": str(e),
            "issues": [],
            "count": 0
        }

@app.get("/api/critical-services/statistics")
async def get_critical_services_statistics():
    """Get statistics about critical services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return {
                "status": "error",
                "message": "Critical services monitor not initialized"
            }
        
        stats = monitor.get_statistics()
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting critical services statistics: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/critical-services/ignore")
async def ignore_alert(data: dict = Body(...)):
    """Ignore an alert and send notification to Discord"""
    try:
        logger.info(f"Ignore alert endpoint called with data: {data}")
        issue = data.get('issue', {})
        
        if not issue:
            logger.error("No issue provided in ignore request")
            return {
                "status": "error",
                "message": "No issue provided"
            }
        
        # Create alert ID (stable identifier without timestamp)
        service = issue.get('service', 'unknown')
        message = issue.get('message', '')
        message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
        alert_id = (service, message_hash)  # Stable identifier
        timestamp = issue.get('timestamp', '')  # Keep for display purposes
        
        logger.info(f"Ignoring alert: {alert_id}")
        
        # Add to ignored alerts
        ignored_alerts.add(alert_id)
        
        # Send Discord notification
        severity = issue.get('severity', issue.get('level', 'CRITICAL'))
        discord_message = f"🚫 **Alert Ignored**\n\n"
        discord_message += f"**Service:** {service}\n"
        discord_message += f"**Severity:** {severity}\n"
        discord_message += f"**Message:** {message[:200]}\n"
        discord_message += f"**Time:** {timestamp}\n"
        discord_message += f"\n*This alert has been ignored and will no longer appear in the dashboard.*"
        
        send_discord_alert(discord_message)
        
        logger.info(f"Alert ignored successfully: {service} - {message[:50]}")
        
        return {
            "status": "success",
            "message": "Alert ignored successfully",
            "alert_id": f"{timestamp}_{service}_{message_hash}"
        }
    
    except Exception as e:
        logger.error(f"Error ignoring alert: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/gemini/analyze-log")
async def analyze_single_log(request: GeminiAnalyzeRequest):
    """Analyze a single log entry using Gemini AI"""
    try:
        # Use the global gemini_analyzer from the module
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        if not _gemini_analyzer:
            logger.error("Gemini analyzer not initialized")
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized. Check GEMINI_API_KEY"
            }
        
        log_entry = request.log_entry
        
        if not log_entry:
            logger.error("No log entry provided")
            return {
                "status": "error",
                "message": "No log entry provided"
            }
        
        logger.info(f"Analyzing log entry: service={log_entry.get('service')}, message={log_entry.get('message', '')[:50]}")
        
        # Analyze the log
        analysis = _gemini_analyzer.analyze_error_log(log_entry)
        
        logger.info(f"Analysis result status: {analysis.get('status')}")
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing log: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/gemini/analyze-pattern")
async def analyze_log_pattern(request: GeminiAnalyzeRequest):
    """Analyze multiple logs for patterns using Gemini AI"""
    try:
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        if not _gemini_analyzer:
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized"
            }
        
        log_entries = request.logs or []
        limit = request.limit or 10
        
        if not log_entries:
            return {
                "status": "error",
                "message": "No log entries provided"
            }
        
        # Analyze patterns
        analysis = _gemini_analyzer.analyze_multiple_logs(log_entries, limit=limit)
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing log pattern: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/gemini/analyze-service/{service_name}")
async def analyze_service_health(service_name: str, limit: int = 50):
    """Analyze overall health of a service using Gemini AI"""
    try:
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        from centralized_logger import centralized_logger as _centralized_logger
        
        if not _gemini_analyzer:
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized"
            }
        
        if not _centralized_logger:
            return {
                "status": "error",
                "message": "Centralized logger not initialized"
            }
        
        # Get logs for the service
        logs = _centralized_logger.get_logs_by_service(service_name, limit=limit)
        
        if not logs:
            return {
                "status": "error",
                "message": f"No logs found for service: {service_name}"
            }
        
        # Analyze service health
        analysis = _gemini_analyzer.analyze_service_health(service_name, logs)
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing service health: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/gemini/quick-analyze")
async def quick_analyze_recent_errors():
    """Quick analysis of recent errors from centralized logs or Fluent Bit"""
    try:
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        
        if not _gemini_analyzer:
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized. Please configure GEMINI_API_KEY."
            }
        
        # Try to get logs from centralized logger first
        error_logs = []
        try:
            from centralized_logger import centralized_logger as _centralized_logger
            if _centralized_logger:
                logs = _centralized_logger.get_recent_logs(limit=50)
                error_logs = [log for log in logs if log.get("level", "").upper() in ["ERROR", "CRITICAL", "FATAL", "ERR"]]
        except Exception as e:
            logger.debug(f"Could not get logs from centralized logger: {e}")
        
        # If no errors from centralized logger, try Fluent Bit
        if not error_logs:
            try:
                import fluent_bit_reader
                if fluent_bit_reader.fluent_bit_reader:
                    reader = fluent_bit_reader.fluent_bit_reader
                    reader.refresh_logs()
                    all_logs = reader.get_recent_logs(limit=50)
                    error_logs = [log for log in all_logs if log.get("level", "").upper() in ["ERROR", "CRITICAL", "FATAL", "ERR"]]
            except Exception as e:
                logger.debug(f"Could not get logs from Fluent Bit: {e}")
        
        # If still no errors, get any recent logs (warnings included)
        if not error_logs:
            try:
                from centralized_logger import centralized_logger as _centralized_logger
                if _centralized_logger:
                    logs = _centralized_logger.get_recent_logs(limit=20)
                    # Include warnings as well
                    error_logs = [log for log in logs if log.get("level", "").upper() in ["ERROR", "CRITICAL", "FATAL", "ERR", "WARNING", "WARN"]]
            except Exception as e:
                logger.debug(f"Could not get logs for warnings: {e}")
        
        if not error_logs:
            return {
                "status": "success",
                "message": "No recent errors or warnings found to analyze",
                "pattern_analysis": {
                    "common_issues": "No issues detected in recent logs.",
                    "timeline": "System appears to be running normally.",
                    "correlation": "No error patterns detected.",
                    "recommendations": "Continue monitoring system health.",
                    "full_analysis": "No recent errors or warnings found in the logs."
                },
                "logs_analyzed": 0
            }
        
        # Analyze errors (limit to 10 most recent)
        analysis = _gemini_analyzer.analyze_multiple_logs(error_logs[:10], limit=10)
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error in quick analyze: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/cli/execute")
async def execute_cli_endpoint(request: CLIExecuteRequest):
    """Execute CLI command with enhanced command set"""
    command = request.command.strip()
    
    if not command:
        return {"error": "No command provided"}
    
    # Handle command aliases
    aliases = {
        "h": "help",
        "ll": "ls -la",
        "l": "ls",
        "c": "clear",
        "q": "exit",
        "s": "status",
        "svc": "services",
        "ps": "processes",
        "d": "disk",
        "u": "uptime",
        "w": "whoami"
    }
    
    # Expand aliases
    cmd_parts = command.split()
    if cmd_parts and cmd_parts[0] in aliases:
        command = aliases[cmd_parts[0]] + " " + " ".join(cmd_parts[1:])
        cmd_parts = command.split()
    
    # Add to history
    command_history.append({
        "command": command,
        "timestamp": datetime.now().isoformat()
    })
    
    # Security: whitelist allowed commands
    allowed_commands = [
        "help", "status", "services", "processes", "disk", "logs", "restart",
        "start", "stop", "uptime", "whoami", "hostname", "uname", "df", "free",
        "ls", "cat", "tail", "head", "grep", "find", "ps", "kill", "pkill",
        "netstat", "ifconfig", "ss", "ping", "stats", "health", "log", "logtail",
        "logsearch", "blocked", "block", "unblock", "clear", "history", "exit",
        "top", "watch"
    ]
    
    if not cmd_parts or cmd_parts[0] not in allowed_commands:
        # Suggest similar commands
        suggestions = [cmd for cmd in allowed_commands if cmd_parts and cmd_parts[0] in cmd or (cmd_parts and cmd.startswith(cmd_parts[0][:2]))]
        error_msg = f"Command '{cmd_parts[0] if cmd_parts else ''}' not allowed."
        if suggestions:
            error_msg += f"\nDid you mean: {', '.join(suggestions[:5])}?"
        return {"error": error_msg}
    
    # Execute command
    try:
        cmd = cmd_parts[0]
        
        if cmd == "help":
            output = """╔══════════════════════════════════════════════════════════════╗
║              Healing Bot CLI - Available Commands              ║
╚══════════════════════════════════════════════════════════════╝

📊 SYSTEM INFO:
  status, s          - Show system status (CPU, Memory, Disk)
  uptime, u          - Show system uptime
  whoami, w          - Show current user
  hostname           - Show system hostname
  uname              - Show system information
  df                 - Show disk filesystem usage
  free               - Show memory usage
  top                - Show top processes (interactive)

⚙️  SERVICES:
  services, svc      - List all services
  start <service>    - Start a service
  stop <service>     - Stop a service
  restart <service> - Restart a service
  status <service>   - Check service status

🔍 PROCESSES:
  processes, ps      - Show top processes
  kill <pid>        - Kill a process by PID
  pkill <name>      - Kill processes by name

📁 FILES:
  ls [path]         - List directory contents
  cat <file>        - Display file contents
  tail <file>       - Show last lines of file
  head <file>       - Show first lines of file
  grep <pattern>    - Search for pattern
  find <name>       - Find files

🌐 NETWORK:
  netstat            - Show network connections
  ifconfig           - Show network interfaces
  ss                 - Show socket statistics
  ping <host>        - Ping a host

📝 LOGS:
  logs               - Show recent logs
  log <service>      - Show logs for service
  logtail            - Tail recent logs
  logsearch <term>   - Search logs

🛡️  BLOCKED IPS:
  blocked            - List blocked IPs
  block <ip>         - Block an IP address
  unblock <ip>       - Unblock an IP address

📈 MONITORING:
  stats              - Show system statistics
  health             - Show system health status

🔧 UTILITIES:
  clear, c           - Clear terminal
  history            - Show command history
  exit, q            - Exit CLI
  watch <cmd>        - Watch command output

Type 'help <command>' for detailed help on a specific command."""
        
        elif cmd == "status" or cmd == "s":
            metrics = get_system_metrics()
            output = f"""╔══════════════════════════════════════════╗
║         System Status                ║
╠══════════════════════════════════════════╣
║ CPU Usage:     {metrics.get('cpu', 0):>6.1f}%              ║
║ Memory Usage:  {metrics.get('memory', 0):>6.1f}%              ║
║ Disk Usage:    {metrics.get('disk', 0):>6.1f}%              ║
╚══════════════════════════════════════════╝"""
        
        elif cmd == "services" or cmd == "svc":
            services = get_all_services_status()
            if not services:
                output = "No services found."
            else:
                output = "SERVICE NAME                    STATUS\n" + "="*50 + "\n"
                for s in services:
                    status_icon = "🟢" if s.get('status') == 'running' else "🔴"
                    output += f"{status_icon} {s.get('name', 'unknown'):<30} {s.get('status', 'unknown')}\n"
        
        elif cmd == "processes" or cmd == "ps":
            limit = int(cmd_parts[1]) if len(cmd_parts) > 1 and cmd_parts[1].isdigit() else 10
            processes = get_top_processes(limit)
            if not processes:
                output = "No processes found."
            else:
                output = f"{'PID':<8} {'NAME':<25} {'CPU%':<8} {'MEM%':<8}\n" + "="*50 + "\n"
                for p in processes:
                    output += f"{p.get('pid', 0):<8} {p.get('name', 'unknown')[:24]:<25} {p.get('cpu', 0):<8.1f} {p.get('memory', 0):<8.1f}\n"
        
        elif cmd == "disk" or cmd == "d":
            disk = psutil.disk_usage('/')
            total_gb = disk.total // (1024**3)
            used_gb = disk.used // (1024**3)
            free_gb = disk.free // (1024**3)
            output = f"""╔══════════════════════════════════════════╗
║         Disk Usage                    ║
╠══════════════════════════════════════════╣
║ Total:  {total_gb:>6} GB                        ║
║ Used:   {used_gb:>6} GB ({disk.percent:>5.1f}%)              ║
║ Free:   {free_gb:>6} GB                        ║
╚══════════════════════════════════════════╝"""
        
        elif cmd == "df":
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append({
                        'device': partition.device,
                        'mount': partition.mountpoint,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    })
                except PermissionError:
                    continue
            
            if not partitions:
                output = "No disk partitions accessible."
            else:
                output = f"{'DEVICE':<20} {'MOUNT':<20} {'TOTAL':<12} {'USED':<12} {'FREE':<12} {'USE%':<6}\n" + "="*90 + "\n"
                for p in partitions:
                    total_gb = p['total'] // (1024**3)
                    used_gb = p['used'] // (1024**3)
                    free_gb = p['free'] // (1024**3)
                    output += f"{p['device']:<20} {p['mount']:<20} {total_gb:>6} GB   {used_gb:>6} GB   {free_gb:>6} GB   {p['percent']:>5.1f}%\n"
        
        elif cmd == "free":
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            output = f"""╔══════════════════════════════════════════╗
║         Memory Usage                   ║
╠══════════════════════════════════════════╣
║ RAM:                                    ║
║   Total:  {mem.total // (1024**3):>6} GB                        ║
║   Used:   {mem.used // (1024**3):>6} GB ({mem.percent:>5.1f}%)              ║
║   Free:   {mem.available // (1024**3):>6} GB                        ║
║                                          ║
║ Swap:                                   ║
║   Total:  {swap.total // (1024**3):>6} GB                        ║
║   Used:   {swap.used // (1024**3):>6} GB ({swap.percent:>5.1f}%)              ║
║   Free:   {swap.free // (1024**3):>6} GB                        ║
╚══════════════════════════════════════════╝"""
        
        elif cmd == "uptime" or cmd == "u":
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            output = f"System uptime: {days} days, {hours} hours, {minutes} minutes\nBoot time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif cmd == "whoami" or cmd == "w":
            output = os.getenv('USER', os.getenv('USERNAME', 'unknown'))
        
        elif cmd == "hostname":
            output = os.uname().nodename
        
        elif cmd == "uname":
            uname = os.uname()
            output = f"""System: {uname.sysname}
Hostname: {uname.nodename}
Release: {uname.release}
Version: {uname.version}
Machine: {uname.machine}"""
        
        elif cmd == "logs":
            output = "\n".join([f"[{log.get('level', 'INFO')}] {log.get('message', '')}" for log in log_buffer[-10:]])
            if not output:
                output = "No recent logs available."
        
        elif cmd == "restart" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            success = restart_service(service)
            output = f"✅ Service '{service}' restarted successfully" if success else f"❌ Failed to restart service '{service}'"
        
        elif cmd == "start" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            success = start_service(service)
            output = f"✅ Service '{service}' started successfully" if success else f"❌ Failed to start service '{service}'"
        
        elif cmd == "stop" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            success = stop_service(service)
            output = f"✅ Service '{service}' stopped successfully" if success else f"❌ Failed to stop service '{service}'"
        
        elif cmd == "status" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            status_info = check_service_status(service)
            status_icon = "🟢" if status_info.get('status') == 'running' else "🔴"
            output = f"{status_icon} {service}: {status_info.get('status', 'unknown')}"
        
        elif cmd == "kill" and len(cmd_parts) > 1:
            try:
                pid = int(cmd_parts[1])
                os.kill(pid, signal.SIGTERM)
                output = f"✅ Sent SIGTERM to process {pid}"
            except ValueError:
                output = "❌ Invalid PID. Usage: kill <pid>"
            except ProcessLookupError:
                output = f"❌ Process {pid} not found"
            except PermissionError:
                output = f"❌ Permission denied to kill process {pid}"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "pkill" and len(cmd_parts) > 1:
            process_name = cmd_parts[1]
            killed = 0
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if process_name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            killed += 1
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                output = f"✅ Terminated {killed} process(es) matching '{process_name}'"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "ls":
            path = cmd_parts[1] if len(cmd_parts) > 1 else "."
            try:
                path_obj = Path(path).expanduser().resolve()
                if not path_obj.exists():
                    output = f"❌ Path not found: {path}"
                elif path_obj.is_file():
                    output = str(path_obj)
                else:
                    items = sorted(path_obj.iterdir())
                    dirs = [item for item in items if item.is_dir()]
                    files = [item for item in items if item.is_file()]
                    output = ""
                    if dirs:
                        output += "📁 DIRECTORIES:\n"
                        for d in dirs:
                            output += f"  {d.name}/\n"
                    if files:
                        output += "\n📄 FILES:\n" if dirs else "📄 FILES:\n"
                        for f in files:
                            size = f.stat().st_size
                            size_str = f"{size} B" if size < 1024 else f"{size/1024:.1f} KB" if size < 1024**2 else f"{size/(1024**2):.1f} MB"
                            output += f"  {f.name:<40} {size_str:>10}\n"
                    if not dirs and not files:
                        output = "Directory is empty"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "cat" and len(cmd_parts) > 1:
            file_path = cmd_parts[1]
            try:
                path_obj = Path(file_path).expanduser().resolve()
                if not path_obj.exists():
                    output = f"❌ File not found: {file_path}"
                elif path_obj.is_dir():
                    output = f"❌ Is a directory: {file_path}"
                else:
                    with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit output to prevent overwhelming
                        if len(content) > 10000:
                            output = content[:10000] + f"\n\n... (truncated, showing first 10000 characters of {len(content)} total)"
                        else:
                            output = content
            except PermissionError:
                output = f"❌ Permission denied: {file_path}"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "tail" and len(cmd_parts) > 1:
            file_path = cmd_parts[1]
            lines = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 10
            try:
                path_obj = Path(file_path).expanduser().resolve()
                if not path_obj.exists():
                    output = f"❌ File not found: {file_path}"
                else:
                    with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                        all_lines = f.readlines()
                        output = "".join(all_lines[-lines:])
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "head" and len(cmd_parts) > 1:
            file_path = cmd_parts[1]
            lines = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 10
            try:
                path_obj = Path(file_path).expanduser().resolve()
                if not path_obj.exists():
                    output = f"❌ File not found: {file_path}"
                else:
                    with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                        output = "".join([f.readline() for _ in range(lines)])
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "grep" and len(cmd_parts) > 1:
            pattern = cmd_parts[1]
            file_path = cmd_parts[2] if len(cmd_parts) > 2 else None
            try:
                if file_path:
                    path_obj = Path(file_path).expanduser().resolve()
                    if not path_obj.exists():
                        output = f"❌ File not found: {file_path}"
                    else:
                        with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                            matches = [line for line in f if pattern in line]
                            output = "".join(matches[:50])  # Limit to 50 matches
                            if len(matches) > 50:
                                output += f"\n... ({len(matches) - 50} more matches)"
                else:
                    output = "❌ Usage: grep <pattern> <file>"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "find" and len(cmd_parts) > 1:
            search_term = cmd_parts[1]
            search_path = cmd_parts[2] if len(cmd_parts) > 2 else "."
            try:
                path_obj = Path(search_path).expanduser().resolve()
                if not path_obj.exists():
                    output = f"❌ Path not found: {search_path}"
                else:
                    matches = []
                    for item in path_obj.rglob("*"):
                        if search_term.lower() in item.name.lower():
                            matches.append(str(item.relative_to(path_obj)))
                            if len(matches) >= 20:  # Limit results
                                break
                    if matches:
                        output = "\n".join(matches)
                        if len(matches) == 20:
                            output += "\n... (showing first 20 matches)"
                    else:
                        output = f"No files found matching '{search_term}'"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "netstat":
            try:
                connections = psutil.net_connections(kind='inet')
                output = f"{'PROTO':<6} {'LOCAL ADDRESS':<25} {'STATUS':<12}\n" + "="*50 + "\n"
                for conn in connections[:20]:  # Limit to 20 connections
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    status = conn.status if conn.status else ""
                    output += f"{'TCP':<6} {laddr:<25} {status:<12}\n"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "ifconfig":
            try:
                interfaces = psutil.net_if_addrs()
                output = ""
                for interface, addrs in interfaces.items():
                    output += f"\n{interface}:\n"
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            output += f"  IPv4: {addr.address}  Netmask: {addr.netmask}\n"
                        elif addr.family == 10:  # IPv6
                            output += f"  IPv6: {addr.address}\n"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "ss":
            try:
                connections = psutil.net_connections(kind='inet')
                output = f"{'STATE':<12} {'LOCAL ADDRESS':<25} {'PEER ADDRESS':<25}\n" + "="*70 + "\n"
                for conn in connections[:20]:
                    laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                    raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                    state = conn.status if conn.status else ""
                    output += f"{state:<12} {laddr:<25} {raddr:<25}\n"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "ping" and len(cmd_parts) > 1:
            host = cmd_parts[1]
            count = int(cmd_parts[2]) if len(cmd_parts) > 2 and cmd_parts[2].isdigit() else 4
            try:
                result = subprocess.run(
                    ["ping", "-c", str(count), host],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout if result.returncode == 0 else result.stderr
            except subprocess.TimeoutExpired:
                output = f"❌ Ping timeout for {host}"
            except FileNotFoundError:
                output = "❌ ping command not available"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "stats":
            metrics = get_system_metrics()
            processes = get_top_processes(5)
            output = f"""╔══════════════════════════════════════════╗
║         System Statistics              ║
╠══════════════════════════════════════════╣
║ CPU:     {metrics.get('cpu', 0):>6.1f}%                        ║
║ Memory:  {metrics.get('memory', 0):>6.1f}%                        ║
║ Disk:    {metrics.get('disk', 0):>6.1f}%                        ║
╠══════════════════════════════════════════╣
║ Top Processes:                          ║
"""
            for p in processes[:5]:
                output += f"║   {p.get('name', 'unknown')[:30]:<30} CPU: {p.get('cpu', 0):>5.1f}% ║\n"
            output += "╚══════════════════════════════════════════╝"
        
        elif cmd == "health":
            metrics = get_system_metrics()
            health_status = "✅ Healthy"
            issues = []
            if metrics.get('cpu', 0) > 90:
                issues.append("High CPU usage")
            if metrics.get('memory', 0) > 90:
                issues.append("High memory usage")
            if metrics.get('disk', 0) > 90:
                issues.append("High disk usage")
            
            if issues:
                health_status = f"⚠️  Warning: {', '.join(issues)}"
            
            output = f"""System Health: {health_status}
CPU: {metrics.get('cpu', 0):.1f}%
Memory: {metrics.get('memory', 0):.1f}%
Disk: {metrics.get('disk', 0):.1f}%"""
        
        elif cmd == "log" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            try:
                from centralized_logger import centralized_logger
                if centralized_logger:
                    logs = centralized_logger.get_recent_logs(limit=20)
                    service_logs = [log for log in logs if service.lower() in str(log.get('service', '')).lower()]
                    if service_logs:
                        output = "\n".join([f"[{log.get('timestamp', '')}] {log.get('message', '')}" for log in service_logs[:20]])
                    else:
                        output = f"No logs found for service: {service}"
                else:
                    output = "Centralized logging not available"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "logtail":
            try:
                from centralized_logger import centralized_logger
                if centralized_logger:
                    logs = centralized_logger.get_recent_logs(limit=20)
                    output = "\n".join([f"[{log.get('timestamp', '')}] [{log.get('service', 'unknown')}] {log.get('message', '')}" for log in logs])
                else:
                    output = "Centralized logging not available"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "logsearch" and len(cmd_parts) > 1:
            search_term = cmd_parts[1]
            try:
                from centralized_logger import centralized_logger
                if centralized_logger:
                    logs = centralized_logger.get_recent_logs(limit=100)
                    matches = [log for log in logs if search_term.lower() in str(log.get('message', '')).lower()]
                    if matches:
                        output = "\n".join([f"[{log.get('timestamp', '')}] {log.get('message', '')}" for log in matches[:20]])
                    else:
                        output = f"No logs found matching: {search_term}"
                else:
                    output = "Centralized logging not available"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "blocked":
            try:
                blocked_ips = blocked_ips_db.get_blocked_ips(include_unblocked=False)
                if not blocked_ips:
                    output = "No blocked IPs"
                else:
                    output = f"{'IP ADDRESS':<20} {'THREAT LEVEL':<15} {'BLOCKED AT':<20} {'REASON':<30}\n" + "="*90 + "\n"
                    for ip_data in blocked_ips[:20]:
                        ip = ip_data.get('ip_address', 'unknown')
                        threat = ip_data.get('threat_level', 'Unknown')
                        blocked_at = ip_data.get('blocked_at', '')
                        reason = ip_data.get('reason', '')[:28]
                        if blocked_at:
                            try:
                                dt = datetime.fromisoformat(blocked_at.replace('Z', '+00:00'))
                                blocked_at = dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                pass
                        output += f"{ip:<20} {threat:<15} {blocked_at:<20} {reason:<30}\n"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "block" and len(cmd_parts) > 1:
            ip = cmd_parts[1]
            threat_level = cmd_parts[2] if len(cmd_parts) > 2 else "High"
            try:
                success = blocked_ips_db.block_ip(ip, threat_level=threat_level, blocked_by="cli_user")
                output = f"✅ IP {ip} blocked successfully" if success else f"❌ Failed to block IP {ip}"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "unblock" and len(cmd_parts) > 1:
            ip = cmd_parts[1]
            try:
                success = blocked_ips_db.unblock_ip(ip, unblocked_by="cli_user")
                output = f"✅ IP {ip} unblocked successfully" if success else f"❌ Failed to unblock IP {ip}"
            except Exception as e:
                output = f"❌ Error: {str(e)}"
        
        elif cmd == "clear" or cmd == "c":
            output = "CLEAR"  # Special marker for frontend to clear output
        
        elif cmd == "history":
            if not command_history:
                output = "No command history"
            else:
                output = "COMMAND HISTORY:\n" + "="*60 + "\n"
                for i, hist in enumerate(command_history[-20:], 1):
                    timestamp = hist.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            timestamp = dt.strftime('%H:%M:%S')
                        except:
                            pass
                    output += f"{i:>3}. [{timestamp}] {hist.get('command', '')}\n"
        
        elif cmd == "exit" or cmd == "q":
            output = "Exiting CLI... (This is a web interface, use 'clear' to clear the terminal)"
        
        elif cmd == "top":
            processes = get_top_processes(10)
            output = f"{'PID':<8} {'NAME':<25} {'CPU%':<8} {'MEM%':<8} {'STATUS':<10}\n" + "="*65 + "\n"
            for p in processes:
                output += f"{p.get('pid', 0):<8} {p.get('name', 'unknown')[:24]:<25} {p.get('cpu', 0):<8.1f} {p.get('memory', 0):<8.1f} {'running':<10}\n"
        
        elif cmd == "watch" and len(cmd_parts) > 1:
            # For watch, we'll execute the sub-command once (real watch would need polling)
            watch_cmd = " ".join(cmd_parts[1:])
            # Recursively call with the sub-command
            watch_data = {"command": watch_cmd}
            result = await execute_cli_endpoint(watch_data)
            output = f"[Watch mode - single execution]\n{result.get('output', result.get('error', ''))}"
        
        else:
            output = f"Invalid command: {cmd}. Type 'help' for available commands."
        
        return {"output": output, "command": command}
    
    except Exception as e:
        logger.error(f"Error executing CLI command: {e}", exc_info=True)
        return {"error": str(e)}

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return CONFIG

@app.post("/api/config")
async def update_config(data: dict):
    """Update configuration"""
    # Store old auto_restart value before updating
    old_auto_restart = CONFIG.get("auto_restart", True)
    
    # Check if auto_restart is being disabled
    if "auto_restart" in data and not data["auto_restart"] and old_auto_restart:
        logger.info("⏸️ Auto-restart has been disabled - auto-start process will stop")
        log_event("info", "Auto-restart disabled - service auto-start process stopped")
        send_discord_alert("⏸️ Auto-restart disabled - service auto-start process stopped")
    
    # Update the configuration
    CONFIG.update(data)
    
    # Log when auto-restart is enabled (checking new value)
    if "auto_restart" in data and data["auto_restart"] and not old_auto_restart:
        logger.info("▶️ Auto-restart has been enabled - auto-start process will resume")
        log_event("info", "Auto-restart enabled - service auto-start process active")
        send_discord_alert("▶️ Auto-restart enabled - service auto-start process active")
    
    return {"success": True, "config": CONFIG}

# ============================================================================
# DDoS Detection & ML Model Endpoints
# ============================================================================

@app.get("/api/metrics/ml")
async def get_ml_metrics():
    """Get ML model performance metrics"""
    try:
        metrics = fetch_ml_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error in /api/metrics/ml: {e}")
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "prediction_time_ms": 0.0,
            "throughput": 0.0
        }

@app.get("/api/metrics/attacks")
async def get_attack_metrics():
    """Get DDoS attack statistics"""
    try:
        stats = get_attack_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error in /api/metrics/attacks: {e}")
        return {
            "total_detections": 0,
            "ddos_attacks": 0,
            "false_positives": 0,
            "detection_rate": 0.0,
            "attack_types": {},
            "top_source_ips": {}
        }

# ============================================================================
# Predictive Maintenance Endpoints
# ============================================================================

def load_predictive_model():
    """Load predictive maintenance model if available"""
    try:
        artifacts_dir = Path(__file__).parent.parent.parent / "model" / "artifacts"
        latest_path = artifacts_dir / "latest"
        
        # Handle case where 'latest' might be a text file, symlink, or directory
        if latest_path.exists():
            # If it's a symlink, resolve it
            if latest_path.is_symlink():
                target_dir = latest_path.readlink()
                # If it's a relative symlink, resolve it relative to artifacts_dir
                if not target_dir.is_absolute():
                    target_dir = artifacts_dir / target_dir
                model_path = target_dir / "model_loader.py"
            # If it's a regular file (text file), read the version name
            elif latest_path.is_file():
                try:
                    version_name = latest_path.read_text().strip()
                    # Remove quotes if present
                    version_name = version_name.strip('"\'')
                    target_dir = artifacts_dir / version_name
                    model_path = target_dir / "model_loader.py"
                    logger.info(f"Found 'latest' as text file pointing to {version_name}")
                except Exception as e:
                    logger.warning(f"Could not read version from 'latest' file: {e}")
                    return None
            # If it's a directory, use it directly
            else:
                model_path = latest_path / "model_loader.py"
            
            if model_path.exists() and model_path.is_file():
                import importlib.util
                spec = importlib.util.spec_from_file_location("model_loader", model_path)
                model_loader = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(model_loader)
                logger.info(f"Successfully loaded predictive model from {model_path}")
                return model_loader
            else:
                logger.warning(f"Model loader file not found at {model_path}")
                return None
        else:
            logger.debug(f"Model artifacts directory 'latest' not found at {latest_path}")
        return None
    except Exception as e:
        logger.warning(f"Could not load predictive model: {e}", exc_info=True)
        return None

predictive_model = load_predictive_model()

@app.get("/api/predict-failure-risk")
async def predict_failure_risk():
    """Get current failure risk score based on system metrics"""
    try:
        if predictive_model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Predictive model not available",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown",
                "message": "Train model first using model/train_xgboost_model.py"
            }
        
        # Check if model is actually loaded
        if not hasattr(predictive_model, 'model') or predictive_model.model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Model not loaded",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown",
                "message": "Model file exists but model failed to load"
            }
        
        # Check if model functions exist
        if not hasattr(predictive_model, 'predict_failure_risk'):
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Model functions not available",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown"
            }
        
        # Get current system metrics
        metrics = get_system_metrics()
        
        # Add log pattern metrics
        metrics['error_count'] = 0  # Would be calculated from logs
        metrics['warning_count'] = 0
        metrics['service_failures'] = 0
        
        # Predict risk
        result = predictive_model.predict_failure_risk(metrics)
        
        # Ensure all required fields are present
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        if 'risk_percentage' not in result:
            result['risk_percentage'] = result.get('risk_score', 0.0) * 100
        if 'risk_level' not in result:
            risk_score = result.get('risk_score', 0.0)
            if risk_score > 0.7:
                result['risk_level'] = 'High'
            elif risk_score > 0.5:
                result['risk_level'] = 'Medium'
            elif risk_score > 0.3:
                result['risk_level'] = 'Low'
            else:
                result['risk_level'] = 'Very Low'
        
        return result
    except Exception as e:
        logger.error(f"Error predicting failure risk: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "risk_score": 0.0,
            "risk_percentage": 0.0,
            "has_early_warning": False,
            "is_high_risk": False,
            "risk_level": "Unknown"
        }

@app.get("/api/get-early-warnings")
async def get_early_warnings():
    """Get list of active early warning indicators"""
    try:
        if predictive_model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Predictive model not available",
                "warnings": [],
                "has_warnings": False,
                "warning_count": 0
            }
        
        # Check if model is actually loaded (warnings can work without model)
        # But if model exists, check if it's loaded
        if hasattr(predictive_model, 'model') and predictive_model.model is None:
            # Still return warnings based on system metrics even if model isn't loaded
            pass
        
        # Check if demo metrics are available (for demo mode)
        global _last_demo_metrics
        if _last_demo_metrics and isinstance(_last_demo_metrics, dict) and len(_last_demo_metrics) > 0:
            # Use demo metrics for warnings
            metrics = _last_demo_metrics.copy()
            logger.debug(f"Using demo metrics for early warnings: {metrics}")
        else:
        # Get current system metrics
            system_metrics = get_system_metrics()
            # Normalize field names to match model expectations
            metrics = {
                'cpu_percent': system_metrics.get('cpu', system_metrics.get('cpu_percent', 0)),
                'memory_percent': system_metrics.get('memory', system_metrics.get('memory_percent', 0)),
                'disk_percent': system_metrics.get('disk', system_metrics.get('disk_percent', 0)),
                'error_count': system_metrics.get('error_count', 0),
                'warning_count': system_metrics.get('warning_count', 0),
                'service_failures': system_metrics.get('service_failures', 0),
                'network_in_mbps': system_metrics.get('network_in_mbps', 0),
                'network_out_mbps': system_metrics.get('network_out_mbps', 0)
            }
        
        # Ensure all required fields are present and normalize field names
        if 'cpu_percent' not in metrics:
            metrics['cpu_percent'] = metrics.get('cpu', 0)
        if 'memory_percent' not in metrics:
            metrics['memory_percent'] = metrics.get('memory', 0)
        if 'disk_percent' not in metrics:
            metrics['disk_percent'] = metrics.get('disk', 0)
        if 'error_count' not in metrics:
            metrics['error_count'] = 0
        if 'warning_count' not in metrics:
            metrics['warning_count'] = 0
        if 'service_failures' not in metrics:
            metrics['service_failures'] = 0
        
        # Check if model functions exist
        if not hasattr(predictive_model, 'get_early_warnings'):
            # Return basic warnings based on metrics (demo or real)
            warnings = []
            cpu = metrics.get('cpu_percent', metrics.get('cpu', 0))
            memory = metrics.get('memory_percent', metrics.get('memory', 0))
            disk = metrics.get('disk_percent', metrics.get('disk', 0))
            
            if cpu > 90:
                warnings.append({
                    'type': 'cpu_high',
                    'severity': 'high',
                    'message': f"CPU usage at {cpu:.1f}% - Critical threshold exceeded"
                })
            elif cpu > 75:
                warnings.append({
                    'type': 'cpu_elevated',
                    'severity': 'medium',
                    'message': f"CPU usage at {cpu:.1f}% - Elevated load detected"
                })
            
            if memory > 90:
                warnings.append({
                    'type': 'memory_high',
                    'severity': 'high',
                    'message': f"Memory usage at {memory:.1f}% - Critical threshold exceeded"
                })
            elif memory > 80:
                warnings.append({
                    'type': 'memory_elevated',
                    'severity': 'medium',
                    'message': f"Memory usage at {memory:.1f}% - Elevated usage detected"
                })
            
            if disk > 95:
                warnings.append({
                    'type': 'disk_high',
                    'severity': 'high',
                    'message': f"Disk usage at {disk:.1f}% - Critical threshold exceeded"
                })
            elif disk > 85:
                warnings.append({
                    'type': 'disk_elevated',
                    'severity': 'medium',
                    'message': f"Disk usage at {disk:.1f}% - Elevated usage detected"
                })
            
            # Check error and warning counts
            error_count = metrics.get('error_count', 0)
            warning_count = metrics.get('warning_count', 0)
            service_failures = metrics.get('service_failures', 0)
            
            if error_count > 10:
                warnings.append({
                    'type': 'error_spike',
                    'severity': 'high',
                    'message': f"High error count: {error_count} errors detected"
                })
            elif error_count > 5:
                warnings.append({
                    'type': 'error_elevated',
                    'severity': 'medium',
                    'message': f"Elevated error count: {error_count} errors"
                })
            
            if warning_count > 20:
                warnings.append({
                    'type': 'warning_spike',
                    'severity': 'medium',
                    'message': f"High warning count: {warning_count} warnings"
                })
            
            if service_failures > 0:
                warnings.append({
                    'type': 'service_failure',
                    'severity': 'high',
                    'message': f"Service failures detected: {service_failures} service(s) failed"
                })
            
            return {
                "timestamp": datetime.now().isoformat(),
                "warnings": warnings,
                "has_warnings": len(warnings) > 0,
                "warning_count": len(warnings)
            }
        
        # Get warnings using model function
        try:
            # Log metrics being sent to model
            logger.debug(f"Calling get_early_warnings with metrics: CPU={metrics.get('cpu_percent', 0)}%, Memory={metrics.get('memory_percent', 0)}%, Disk={metrics.get('disk_percent', 0)}%, Errors={metrics.get('error_count', 0)}")
            result = predictive_model.get_early_warnings(metrics)
            logger.info(f"Model get_early_warnings returned {result.get('warning_count', 0)} warnings: {result}")
            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.error(f"Model get_early_warnings returned non-dict: {type(result)}")
                raise ValueError(f"Model function returned {type(result)}, expected dict")
        except Exception as e:
            logger.error(f"Error calling model get_early_warnings: {e}")
            # If model function fails, use fallback warnings
            warnings = []
            cpu = metrics.get('cpu_percent', 0)
            memory = metrics.get('memory_percent', 0)
            disk = metrics.get('disk_percent', 0)
            error_count = metrics.get('error_count', 0)
            warning_count = metrics.get('warning_count', 0)
            service_failures = metrics.get('service_failures', 0)
            
            if cpu > 90:
                warnings.append({'type': 'cpu_high', 'severity': 'high', 'message': f"CPU usage at {cpu:.1f}% - Critical threshold exceeded"})
            elif cpu > 75:
                warnings.append({'type': 'cpu_elevated', 'severity': 'medium', 'message': f"CPU usage at {cpu:.1f}% - Elevated load detected"})
            
            if memory > 90:
                warnings.append({'type': 'memory_high', 'severity': 'high', 'message': f"Memory usage at {memory:.1f}% - Critical threshold exceeded"})
            elif memory > 80:
                warnings.append({'type': 'memory_elevated', 'severity': 'medium', 'message': f"Memory usage at {memory:.1f}% - Elevated usage detected"})
            
            if disk > 95:
                warnings.append({'type': 'disk_high', 'severity': 'high', 'message': f"Disk usage at {disk:.1f}% - Critical threshold exceeded"})
            elif disk > 85:
                warnings.append({'type': 'disk_elevated', 'severity': 'medium', 'message': f"Disk usage at {disk:.1f}% - Elevated usage detected"})
            
            if error_count > 10:
                warnings.append({'type': 'error_spike', 'severity': 'high', 'message': f"High error count: {error_count} errors detected"})
            elif error_count > 5:
                warnings.append({'type': 'error_elevated', 'severity': 'medium', 'message': f"Elevated error count: {error_count} errors"})
            
            if warning_count > 20:
                warnings.append({'type': 'warning_spike', 'severity': 'medium', 'message': f"High warning count: {warning_count} warnings"})
            
            if service_failures > 0:
                warnings.append({'type': 'service_failure', 'severity': 'high', 'message': f"Service failures detected: {service_failures} service(s) failed"})
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "warnings": warnings,
                "has_warnings": len(warnings) > 0,
                "warning_count": len(warnings)
            }
        
        # Ensure all required fields are present
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        
        # Ensure warnings list exists
        if 'warnings' not in result:
            result['warnings'] = []
        
        # Recalculate counts to ensure they match
        warning_count = len(result.get('warnings', []))
        result['warning_count'] = warning_count
        result['has_warnings'] = warning_count > 0
        
        # If no warnings from model but metrics indicate issues, add fallback warnings
        if warning_count == 0:
            cpu = metrics.get('cpu_percent', 0)
            memory = metrics.get('memory_percent', 0)
            disk = metrics.get('disk_percent', 0)
            error_count = metrics.get('error_count', 0)
            warning_count_val = metrics.get('warning_count', 0)
            service_failures = metrics.get('service_failures', 0)
            
            # Add warnings if thresholds are exceeded (even if model didn't catch them)
            fallback_warnings = []
            if cpu > 90:
                fallback_warnings.append({'type': 'cpu_high', 'severity': 'high', 'message': f"CPU usage at {cpu:.1f}% - Critical threshold exceeded"})
            elif cpu > 75:
                fallback_warnings.append({'type': 'cpu_elevated', 'severity': 'medium', 'message': f"CPU usage at {cpu:.1f}% - Elevated load detected"})
            
            if memory > 90:
                fallback_warnings.append({'type': 'memory_high', 'severity': 'high', 'message': f"Memory usage at {memory:.1f}% - Critical threshold exceeded"})
            elif memory > 80:
                fallback_warnings.append({'type': 'memory_elevated', 'severity': 'medium', 'message': f"Memory usage at {memory:.1f}% - Elevated usage detected"})
            
            if disk > 95:
                fallback_warnings.append({'type': 'disk_high', 'severity': 'high', 'message': f"Disk usage at {disk:.1f}% - Critical threshold exceeded"})
            elif disk > 85:
                fallback_warnings.append({'type': 'disk_elevated', 'severity': 'medium', 'message': f"Disk usage at {disk:.1f}% - Elevated usage detected"})
            
            if error_count > 10:
                fallback_warnings.append({'type': 'error_spike', 'severity': 'high', 'message': f"High error count: {error_count} errors detected"})
            elif error_count > 5:
                fallback_warnings.append({'type': 'error_elevated', 'severity': 'medium', 'message': f"Elevated error count: {error_count} errors"})
            
            if warning_count_val > 20:
                fallback_warnings.append({'type': 'warning_spike', 'severity': 'medium', 'message': f"High warning count: {warning_count_val} warnings"})
            
            if service_failures > 0:
                fallback_warnings.append({'type': 'service_failure', 'severity': 'high', 'message': f"Service failures detected: {service_failures} service(s) failed"})
            
            if fallback_warnings:
                logger.warning(f"Model returned no warnings but metrics indicate issues. Adding {len(fallback_warnings)} fallback warnings: CPU={cpu}%, Memory={memory}%, Disk={disk}%, Errors={error_count}, Failures={service_failures}")
                # Use fallback warnings
                result['warnings'] = fallback_warnings
                result['warning_count'] = len(fallback_warnings)
                result['has_warnings'] = True
        
        logger.debug(f"Final warnings result: {result}")
        
        # Send Discord notification for new/changed warnings (rate-limited)
        warning_count = result.get('warning_count', 0)
        current_warning_types = set(w.get('type', '') for w in result.get('warnings', []))
        
        # Only send notification if:
        # 1. There are warnings AND
        # 2. (Warning count changed OR warning types changed) AND
        # 3. Not sent in last 5 minutes (rate limiting)
        should_send_notification = False
        global _last_sent_warnings, _last_sent_warning_count, _last_warning_notification_time
        
        if warning_count > 0:
            current_time = datetime.now()
            time_since_last = None
            if _last_warning_notification_time:
                time_since_last = (current_time - _last_warning_notification_time).total_seconds() / 60
            
            # Check if warnings changed significantly
            warnings_changed = (
                warning_count != _last_sent_warning_count or
                current_warning_types != _last_sent_warnings
            )
            
            # Send if warnings changed and (never sent before OR 5+ minutes since last)
            if warnings_changed and (time_since_last is None or time_since_last >= 5):
                should_send_notification = True
                _last_sent_warnings = current_warning_types.copy()
                _last_sent_warning_count = warning_count
                _last_warning_notification_time = current_time
        elif warning_count == 0 and _last_sent_warning_count > 0:
            # Warnings cleared - reset tracking
            _last_sent_warnings = set()
            _last_sent_warning_count = 0
        
        if should_send_notification:
            try:
                send_early_warnings_discord_notification(
                    result.get('warnings', []),
                    warning_count,
                    metrics
                )
            except Exception as e:
                logger.error(f"Error sending Discord notification for warnings: {e}")
        
        return result
    except Exception as e:
        logger.error(f"Error getting early warnings: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "warnings": [],
            "has_warnings": False,
            "warning_count": 0
        }

@app.get("/api/predict-time-to-failure")
async def predict_time_to_failure():
    """Predict estimated hours until next failure"""
    try:
        if predictive_model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Predictive model not available",
                "hours_until_failure": None,
                "message": "No failure predicted - model not available"
            }
        
        # Check if model is actually loaded
        if not hasattr(predictive_model, 'model') or predictive_model.model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Model not loaded",
                "hours_until_failure": None,
                "message": "No failure predicted - model failed to load"
            }
        
        # Check if model functions exist
        if not hasattr(predictive_model, 'predict_time_to_failure'):
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Model functions not available",
                "hours_until_failure": None,
                "message": "No failure predicted"
            }
        
        # Check if demo metrics are available (for demo mode)
        global _last_demo_metrics
        if _last_demo_metrics and isinstance(_last_demo_metrics, dict) and len(_last_demo_metrics) > 0:
            # Use demo metrics for time-to-failure prediction
            metrics = _last_demo_metrics.copy()
            logger.debug(f"Using demo metrics for time-to-failure: {metrics}")
        else:
        # Get current system metrics
            system_metrics = get_system_metrics()
            # Normalize field names to match model expectations
            metrics = {
                'cpu_percent': system_metrics.get('cpu', system_metrics.get('cpu_percent', 0)),
                'memory_percent': system_metrics.get('memory', system_metrics.get('memory_percent', 0)),
                'disk_percent': system_metrics.get('disk', system_metrics.get('disk_percent', 0)),
                'error_count': system_metrics.get('error_count', 0),
                'warning_count': system_metrics.get('warning_count', 0),
                'service_failures': system_metrics.get('service_failures', 0),
                'network_in_mbps': system_metrics.get('network_in_mbps', 0),
                'network_out_mbps': system_metrics.get('network_out_mbps', 0)
            }
        
        # Ensure all required fields are present and normalize field names
        if 'cpu_percent' not in metrics:
            metrics['cpu_percent'] = metrics.get('cpu', 0)
        if 'memory_percent' not in metrics:
            metrics['memory_percent'] = metrics.get('memory', 0)
        if 'disk_percent' not in metrics:
            metrics['disk_percent'] = metrics.get('disk', 0)
        if 'error_count' not in metrics:
            metrics['error_count'] = 0
        if 'warning_count' not in metrics:
            metrics['warning_count'] = 0
        if 'service_failures' not in metrics:
            metrics['service_failures'] = 0
        
        # Predict time to failure
        result = predictive_model.predict_time_to_failure(metrics)
        
        # Ensure timestamp is present
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        
        # Send Discord notification for significant time-to-failure changes
        hours_until_failure = result.get('hours_until_failure')
        if hours_until_failure is not None:
            global _last_sent_time_to_failure, _last_time_to_failure_notification_time
            
            current_time = datetime.now()
            should_send_notification = False
            
            # Determine if notification should be sent
            if _last_sent_time_to_failure is None:
                # First prediction with a value - send if < 48 hours
                if hours_until_failure < 48:
                    should_send_notification = True
            else:
                # Check if time-to-failure changed significantly
                time_diff = abs(hours_until_failure - _last_sent_time_to_failure)
                time_since_last = None
                if _last_time_to_failure_notification_time:
                    time_since_last = (current_time - _last_time_to_failure_notification_time).total_seconds() / 3600  # in hours
                
                # Send notification if:
                # 1. Time-to-failure decreased significantly (>25% or <6 hours difference) OR
                # 2. Time-to-failure is <24 hours and changed by >2 hours AND
                # 3. Not sent in last 30 minutes (rate limiting for urgent cases) OR 2 hours (for less urgent)
                if hours_until_failure < 24:
                    # Urgent: send if changed by >2 hours and not sent in last 30 minutes
                    if time_diff > 2 and (time_since_last is None or time_since_last >= 0.5):
                        should_send_notification = True
                elif hours_until_failure < 48:
                    # Moderate: send if changed significantly and not sent in last 2 hours
                    if (time_diff > max(6, _last_sent_time_to_failure * 0.25)) and (time_since_last is None or time_since_last >= 2):
                        should_send_notification = True
                else:
                    # Less urgent: send if changed significantly and not sent in last 6 hours
                    if (time_diff > max(12, _last_sent_time_to_failure * 0.3)) and (time_since_last is None or time_since_last >= 6):
                        should_send_notification = True
            
            if should_send_notification:
                try:
                    # Get risk percentage if available from last prediction
                    risk_percentage = None
                    try:
                        risk_response = predictive_model.predict_failure_risk(metrics)
                        risk_percentage = risk_response.get('risk_percentage')
                    except:
                        pass
                    
                    send_time_to_failure_discord_notification(
                        hours_until_failure,
                        result.get('predicted_failure_time'),
                        risk_percentage,
                        metrics
                    )
                    _last_sent_time_to_failure = hours_until_failure
                    _last_time_to_failure_notification_time = current_time
                except Exception as e:
                    logger.error(f"Error sending Discord notification for time-to-failure: {e}")
        elif _last_sent_time_to_failure is not None:
            # Time-to-failure cleared (no failure predicted) - reset tracking
            _last_sent_time_to_failure = None
        
        return result
    except Exception as e:
        logger.error(f"Error predicting time to failure: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "hours_until_failure": None,
            "message": "No failure predicted"
        }

@app.post("/api/predict-anomaly")
async def predict_anomaly(request: Request):
    """Real-time anomaly detection from provided metrics"""
    try:
        if predictive_model is None:
            return {
                "error": "Predictive model not available",
                "is_anomaly": False
            }
        
        data = await request.json()
        metrics = data.get('metrics', {})
        
        # Store for dashboard demo mode
        global _last_demo_metrics
        _last_demo_metrics = metrics
        
        # Predict anomaly
        result = predictive_model.predict_anomaly(metrics)
        return result
    except Exception as e:
        logger.error(f"Error predicting anomaly: {e}")
        return {
            "error": str(e),
            "is_anomaly": False
        }

# Store last demo metrics for dashboard polling
_last_demo_metrics = None

@app.get("/api/get-last-demo-metrics")
async def get_last_demo_metrics():
    """Get last demo metrics sent (for dashboard demo mode)"""
    global _last_demo_metrics
    if _last_demo_metrics:
        return {"metrics": _last_demo_metrics, "timestamp": datetime.now().isoformat()}
    return {"metrics": None}

@app.post("/api/predict-failure-risk-custom")
async def predict_failure_risk_custom(request: Request):
    """Get failure risk score from custom metrics (for demonstrations)"""
    try:
        if predictive_model is None or not hasattr(predictive_model, 'model') or predictive_model.model is None:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Predictive model not available",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown"
            }
        
        if not hasattr(predictive_model, 'predict_failure_risk'):
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Model functions not available",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown"
            }
        
        data = await request.json()
        metrics = data.get('metrics', {})
        
        # Store for dashboard demo mode
        global _last_demo_metrics
        _last_demo_metrics = metrics
        
        # Ensure all required metrics are present
        if not metrics:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "No metrics provided",
                "risk_score": 0.0,
                "risk_percentage": 0.0,
                "has_early_warning": False,
                "is_high_risk": False,
                "risk_level": "Unknown"
            }
        
        # Predict risk with custom metrics
        result = predictive_model.predict_failure_risk(metrics)
        
        # Ensure all required fields are present
        if 'timestamp' not in result:
            result['timestamp'] = datetime.now().isoformat()
        if 'risk_percentage' not in result:
            result['risk_percentage'] = result.get('risk_score', 0.0) * 100
        if 'risk_level' not in result:
            risk_score = result.get('risk_score', 0.0)
            if risk_score > 0.7:
                result['risk_level'] = 'High'
            elif risk_score > 0.5:
                result['risk_level'] = 'Medium'
            elif risk_score > 0.3:
                result['risk_level'] = 'Low'
            else:
                result['risk_level'] = 'Very Low'
        
        return result
    except Exception as e:
        logger.error(f"Error predicting failure risk with custom metrics: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "risk_score": 0.0,
            "risk_percentage": 0.0,
            "has_early_warning": False,
            "is_high_risk": False,
            "risk_level": "Unknown"
        }

@app.get("/api/history/ml")
async def get_ml_history():
    """Get ML model performance history"""
    try:
        return ml_performance_history
    except Exception as e:
        logger.error(f"Error in /api/history/ml: {e}")
        return {
            "timestamps": [],
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1_score": [],
            "prediction_times": []
        }

@app.post("/api/blocking/block")
async def block_ip_ddos(request: BlockIPRequest, additional_data: dict = Body(None)):
    """Block an IP address (DDoS endpoint)"""
    # Use Pydantic model for IP validation, but allow additional fields from body
    ip = request.ip
    if additional_data:
        attack_count = additional_data.get("attack_count", 1)
        threat_level = additional_data.get("threat_level", "Medium")
        attack_type = additional_data.get("attack_type")
        reason = additional_data.get("reason") or request.reason or f"Manual block via dashboard"
        blocked_by = additional_data.get("blocked_by", "dashboard")
    else:
        attack_count = 1
        threat_level = "Medium"
        attack_type = None
        reason = request.reason or f"Manual block via dashboard"
        blocked_by = "dashboard"
    
    try:
        success = block_ip(
            ip=ip,
            attack_count=attack_count,
            threat_level=threat_level,
            attack_type=attack_type,
            reason=reason,
            blocked_by=blocked_by
        )
        
        if success:
            log_event("warning", f"Blocked malicious IP: {ip} ({threat_level})")
            return {"success": True, "ip": ip, "message": "IP blocked successfully"}
        else:
            return {"success": False, "ip": ip, "message": "Failed to block IP"}
    except Exception as e:
        logger.error(f"Error blocking IP {ip}: {e}")
        return {"success": False, "ip": ip, "error": str(e)}

@app.post("/api/ddos/report")
async def report_ddos_detection(data: dict):
    """Report a DDoS detection from external services"""
    try:
        update_ddos_statistics(data)
        log_event("warning", f"DDoS attack detected from {data.get('source_ip', 'unknown')}")
        
        # Send alert if it's an actual attack
        if data.get('is_ddos', False):
            send_discord_alert(
                f"🚨 DDoS Attack Detected!\nSource: {data.get('source_ip', 'unknown')}\nType: {data.get('attack_type', 'Unknown')}",
                "critical"
            )
        
        return {"success": True, "message": "Detection reported successfully"}
    except Exception as e:
        logger.error(f"Error reporting DDoS detection: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# Blocked IPs Management Endpoints
# ============================================================================

@app.get("/api/blocked-ips")
async def get_blocked_ips_list(include_unblocked: bool = False):
    """Get list of all blocked IPs"""
    try:
        ips = blocked_ips_db.get_blocked_ips(include_unblocked=include_unblocked)
        return {"success": True, "blocked_ips": ips, "count": len(ips)}
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return {"success": False, "error": str(e), "blocked_ips": []}

# IMPORTANT: Specific routes MUST come before the generic /{ip_address} route
# Otherwise FastAPI will match "statistics" as an ip_address parameter

@app.get("/api/blocked-ips/statistics")
async def get_blocked_ips_statistics():
    """Get statistics about blocked IPs"""
    try:
        stats = blocked_ips_db.get_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Error getting blocked IPs statistics: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/blocked-ips/unblock")
async def unblock_ip_endpoint(data: dict):
    """Unblock an IP address"""
    ip = data.get("ip")
    unblocked_by = data.get("unblocked_by", "admin")
    reason = data.get("reason", "Manual unblock")
    
    if not ip:
        raise HTTPException(status_code=400, detail="IP address is required")
    
    try:
        success = unblock_ip(ip, unblocked_by=unblocked_by, reason=reason)
        
        if success:
            log_event("info", f"IP {ip} unblocked by {unblocked_by}")
            return {
                "success": True,
                "message": f"IP {ip} unblocked successfully",
                "ip": ip
            }
        else:
            return {
                "success": False,
                "message": f"Failed to unblock IP {ip}",
                "ip": ip
            }
    except Exception as e:
        logger.error(f"Error in unblock endpoint: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/blocked-ips/cleanup")
async def cleanup_old_blocked_ips(days: int = 90):
    """Clean up old unblocked IP records"""
    try:
        deleted = blocked_ips_db.cleanup_old_records(days=days)
        return {
            "success": True,
            "message": f"Cleaned up {deleted} old records",
            "deleted_count": deleted
        }
    except Exception as e:
        logger.error(f"Error cleaning up old records: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/blocked-ips/export")
async def export_blocked_ips(filepath: str = "blocked_ips_export.csv"):
    """Export blocked IPs to CSV"""
    try:
        success = blocked_ips_db.export_to_csv(filepath)
        if success:
            return {
                "success": True,
                "message": f"Exported to {filepath}",
                "filepath": filepath
            }
        else:
            return {"success": False, "message": "Export failed"}
    except Exception as e:
        logger.error(f"Error exporting blocked IPs: {e}")
        return {"success": False, "error": str(e)}

# Generic route with path parameter MUST come LAST
# This catches any IP address like /api/blocked-ips/192.168.1.1
@app.get("/api/blocked-ips/{ip_address}")
async def get_ip_details(ip_address: str):
    """Get detailed information about a specific IP"""
    try:
        ip_info = blocked_ips_db.get_ip_info(ip_address)
        ip_history = blocked_ips_db.get_ip_history(ip_address)
        
        if ip_info:
            return {
                "success": True,
                "ip_info": ip_info,
                "history": ip_history
            }
        else:
            return {"success": False, "error": "IP not found"}
    except Exception as e:
        logger.error(f"Error getting IP details: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# Cloud Simulation & Fault Detection API Endpoints
# ============================================================================

# Initialize cloud simulation components
fault_detector = None
fault_injector = None
container_healer = None
auto_healer = None
root_cause_analyzer = None
container_monitor = None
resource_monitor = None

def initialize_cloud_components():
    """Initialize cloud simulation and fault detection components"""
    global fault_detector, fault_injector, container_healer, auto_healer
    global root_cause_analyzer, container_monitor, resource_monitor
    
    try:
        from fault_detector import initialize_fault_detector
        from fault_injector import initialize_fault_injector
        from container_healer import initialize_container_healer
        try:
            from .healing import initialize_auto_healer
        except ImportError:
            # Fallback to old import path
            from auto_healer import initialize_auto_healer
        from root_cause_analyzer import initialize_root_cause_analyzer
        from container_monitor import ContainerMonitor
        from resource_monitor import ResourceMonitor
        
        # Discord notifier function
        def discord_notifier(message, severity="info", embed_data=None):
            return send_discord_alert(message, severity, embed_data)
        
        # Event emitter for WebSocket (wrapper to make it callable from sync code)
        def event_emitter(event):
            # Schedule async broadcast in the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(broadcast_event(event))
                else:
                    asyncio.run(broadcast_event(event))
            except RuntimeError:
                # No event loop running, create a new one
                asyncio.run(broadcast_event(event))
        
        # Initialize components
        fault_detector = initialize_fault_detector(
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        fault_detector.start_monitoring(interval=30)
        
        fault_injector = initialize_fault_injector()
        container_healer = initialize_container_healer(
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        
        root_cause_analyzer = initialize_root_cause_analyzer(
            gemini_analyzer=_gemini_analyzer
        )
        
        auto_healer = initialize_auto_healer(
            gemini_analyzer=_gemini_analyzer,
            container_healer=container_healer,
            root_cause_analyzer=root_cause_analyzer,
            discord_notifier=discord_notifier,
            event_emitter=event_emitter
        )
        auto_healer.start_monitoring(interval_seconds=60)
        
        container_monitor = ContainerMonitor()
        resource_monitor = ResourceMonitor()
        
        logger.info("✅ Cloud simulation components initialized")
    except Exception as e:
        logger.error(f"Error initializing cloud components: {e}", exc_info=True)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

async def broadcast_event(event: dict):
    """Broadcast event to all WebSocket connections"""
    await manager.broadcast(event)

# Cloud components will be initialized in the startup event handler

@app.websocket("/ws/faults")
async def websocket_faults(websocket: WebSocket):
    """WebSocket endpoint for real-time fault and healing updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            if fault_detector:
                faults = fault_detector.get_detected_faults(limit=10)
                stats = fault_detector.get_fault_statistics()
                
                await websocket.send_json({
                    'type': 'faults_update',
                    'faults': faults,
                    'statistics': stats,
                    'timestamp': datetime.now().isoformat()
                })
            
            if auto_healer:
                history = auto_healer.get_healing_history(limit=10)
                healing_stats = auto_healer.get_healing_statistics()
                
                await websocket.send_json({
                    'type': 'healing_update',
                    'history': history,
                    'statistics': healing_stats,
                    'timestamp': datetime.now().isoformat()
                })
            
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/cloud/services/status")
async def get_cloud_services_status():
    """Get status of all cloud simulation services"""
    try:
        if not container_monitor:
            return {"success": False, "error": "Container monitor not initialized"}
        
        services = container_monitor.get_all_containers_status()
        return {
            "success": True,
            "services": services,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cloud services status: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/cloud/faults")
async def get_detected_faults(limit: int = 50):
    """Get detected faults"""
    try:
        if not fault_detector:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Fault detector not initialized", "faults": [], "statistics": {}}
            )
        
        faults = fault_detector.get_detected_faults(limit=limit)
        stats = fault_detector.get_fault_statistics()
        
        return {
            "success": True,
            "faults": faults or [],
            "statistics": stats or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting detected faults: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "faults": [], "statistics": {}}
        )

@app.get("/api/cloud/resources")
async def get_resource_metrics():
    """Get current resource metrics"""
    try:
        if not resource_monitor:
            return {"success": False, "error": "Resource monitor not initialized"}
        
        resources = resource_monitor.get_all_resources()
        anomalies = resource_monitor.detect_resource_anomalies()
        
        return {
            "success": True,
            "resources": resources,
            "anomalies": anomalies,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting resource metrics: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/cloud/faults/inject")
async def inject_fault(request: Request):
    """Inject a fault for testing"""
    try:
        if not fault_injector:
            return {"success": False, "error": "Fault injector not initialized"}
        
        data = await request.json()
        fault_type = data.get('type', 'crash')
        container = data.get('container', 'cloud-sim-api-server')
        
        if fault_type == 'crash':
            success, message = fault_injector.inject_service_crash(container)
        elif fault_type == 'cpu':
            duration = data.get('duration', 60)
            success, message = fault_injector.inject_cpu_exhaustion(duration)
        elif fault_type == 'memory':
            size = data.get('size', 2.0)
            success, message = fault_injector.inject_memory_exhaustion(size)
        elif fault_type == 'disk':
            size = data.get('size', 5.0)
            success, message = fault_injector.inject_disk_full(size)
        elif fault_type == 'network':
            port = data.get('port')
            success, message = fault_injector.inject_network_issue(container, port)
        else:
            return {"success": False, "error": f"Unknown fault type: {fault_type}"}
        
        return {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error injecting fault: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/cloud/healing/history")
async def get_healing_history(limit: int = 50):
    """Get healing history"""
    try:
        if not auto_healer:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Auto-healer not initialized", "message": "Auto-healing service is not available"}
            )
        
        history = auto_healer.get_healing_history(limit=limit)
        stats = auto_healer.get_healing_statistics()
        
        return {
            "success": True,
            "history": history or [],
            "statistics": stats or {},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting healing history: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "message": "Internal server error while fetching healing history"}
        )

@app.get("/api/auto-healer/status")
async def get_auto_healer_status():
    """Get auto-healer status and configuration"""
    try:
        if not auto_healer:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "message": "Auto-healer not initialized",
                    "auto_healer": None
                }
            )
        
        return {
            "status": "success",
            "auto_healer": {
                "enabled": getattr(auto_healer, 'enabled', True),
                "auto_execute": getattr(auto_healer, 'auto_execute', True),
                "monitoring": getattr(auto_healer, 'running', False),
                "max_attempts": getattr(auto_healer, 'max_healing_attempts', 3),
                "monitoring_interval": getattr(auto_healer, 'monitoring_interval', 60)
            }
        }
    except Exception as e:
        logger.error(f"Error getting auto-healer status: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "auto_healer": None
            }
        )

@app.post("/api/auto-healer/config")
@app.put("/api/auto-healer/config")
async def update_auto_healer_config(request: Request):
    """Update auto-healer configuration"""
    try:
        if not auto_healer:
            return {
                "status": "error",
                "message": "Auto-healer not initialized"
            }
        
        data = await request.json()
        
        # Extract configuration parameters
        enabled = data.get('enabled')
        auto_execute = data.get('auto_execute')
        max_attempts = data.get('max_attempts')
        monitoring_interval = data.get('monitoring_interval')
        
        # Update configuration
        updated_config = auto_healer.update_config(
            enabled=enabled if enabled is not None else None,
            auto_execute=auto_execute if auto_execute is not None else None,
            max_healing_attempts=max_attempts if max_attempts is not None else None,
            monitoring_interval=monitoring_interval if monitoring_interval is not None else None
        )
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "auto_healer": updated_config
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Error updating auto-healer configuration: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/gemini/status")
async def get_gemini_status():
    """Check Gemini API key status and analyzer initialization"""
    # Reload .env file to get latest API key
    load_dotenv(dotenv_path=str(env_path_abs), override=True)
    
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    
    from gemini_log_analyzer import gemini_analyzer as current_analyzer
    
    status = {
        "api_key_configured": bool(api_key and api_key != "your_gemini_api_key_here" and len(api_key) >= 20),
        "api_key_length": len(api_key) if api_key else 0,
        "analyzer_initialized": current_analyzer is not None,
        "model_available": current_analyzer is not None and hasattr(current_analyzer, 'model') and current_analyzer.model is not None,
        "env_file_path": str(env_path_abs),
        "env_file_exists": env_path_abs.exists()
    }
    
    # Try to initialize if API key exists but analyzer is not initialized
    if status["api_key_configured"] and not status["model_available"]:
        try:
            logger.info("Attempting to initialize Gemini analyzer from status endpoint")
            initialize_gemini_analyzer(api_key=api_key)
            from gemini_log_analyzer import gemini_analyzer as current_analyzer
            status["analyzer_initialized"] = current_analyzer is not None
            status["model_available"] = current_analyzer is not None and hasattr(current_analyzer, 'model') and current_analyzer.model is not None
            if status["model_available"]:
                status["message"] = "Gemini analyzer initialized successfully"
            else:
                status["message"] = "Failed to initialize model. Check API key validity."
        except Exception as e:
            status["initialization_error"] = str(e)
            status["message"] = f"Initialization failed: {str(e)}"
    
    if not status["api_key_configured"]:
        status["message"] = "GEMINI_API_KEY not configured in .env file"
    elif not status["model_available"]:
        status["message"] = "Analyzer initialized but model not available. Check API key validity."
    else:
        status["message"] = "Gemini analyzer is ready"
    
    return status

@app.post("/api/cloud/faults/{fault_id}/analyze")
async def analyze_fault_with_ai(fault_id: int):
    """Analyze a fault using AI to get healing instructions"""
    try:
        # Check if fault_detector is initialized
        if fault_detector is None:
            logger.warning("Fault detector not initialized")
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Fault detector not initialized"}
            )
        
        # Get faults safely
        try:
            faults = fault_detector.get_detected_faults(limit=100)
        except Exception as e:
            logger.error(f"Error getting detected faults: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Error retrieving faults: {str(e)}"}
            )
        
        if not faults or fault_id >= len(faults):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Fault not found (requested: {fault_id}, available: {len(faults) if faults else 0})"}
            )
        
        fault = faults[fault_id]
        
        # Reload .env file to get latest API key
        load_dotenv(dotenv_path=str(env_path_abs), override=True)
        
        # Check if Gemini analyzer is available and properly configured
        # Import fresh to get latest state
        from gemini_log_analyzer import gemini_analyzer as current_analyzer
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        # Try to initialize/reinitialize if needed
        if not current_analyzer or (current_analyzer and (not hasattr(current_analyzer, 'model') or current_analyzer.model is None)):
            if api_key and api_key != "your_gemini_api_key_here" and len(api_key) >= 20:
                try:
                    logger.info("Attempting to initialize Gemini analyzer with API key from .env")
                    initialize_gemini_analyzer(api_key=api_key)
                    from gemini_log_analyzer import gemini_analyzer as current_analyzer
                    logger.info(f"Gemini analyzer initialized: {current_analyzer is not None}, model: {current_analyzer.model is not None if current_analyzer else 'N/A'}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini analyzer: {e}", exc_info=True)
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": False,
                            "error": f"AI analyzer initialization failed: {str(e)}\n\nPlease check:\n1. Your GEMINI_API_KEY is valid\n2. You have internet connectivity\n3. The API key has proper permissions",
                            "fault": fault
                        }
                    )
        
        # Check if analyzer has valid model
        if not current_analyzer or not hasattr(current_analyzer, 'model') or current_analyzer.model is None:
            if not api_key or api_key == "your_gemini_api_key_here" or len(api_key) < 20:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": False,
                        "error": "AI analyzer not available. Please configure GEMINI_API_KEY in your .env file.\n\nGet your FREE API key:\n1. Visit: https://aistudio.google.com/app/apikey\n2. Click 'Create API Key'\n3. Copy the key and add to .env file:\n   GEMINI_API_KEY=your_actual_key_here\n4. Restart the monitoring server or reload this page",
                        "fault": fault,
                        "setup_instructions": {
                            "title": "Setup GEMINI_API_KEY",
                            "steps": [
                                "Visit: https://aistudio.google.com/app/apikey",
                                "Click 'Create API Key'",
                                "Copy the key and add to .env file: GEMINI_API_KEY=your_actual_key_here",
                                "Restart the monitoring server or reload this page"
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": False,
                        "error": f"AI analyzer initialization failed even though API key is configured.\n\nAPI key length: {len(api_key)} characters\n\nPlease check:\n1. Your GEMINI_API_KEY is valid and not expired\n2. You have internet connectivity\n3. Restart the monitoring server",
                        "fault": fault
                    }
                )
        
        # Use the current analyzer
        gemini_analyzer = current_analyzer
        
        # Get system metrics for better analysis
        try:
            metrics = get_system_metrics()
        except:
            metrics = None
        
        # Analyze fault with AI
        analysis_result = gemini_analyzer.analyze_cloud_fault(
            fault,
            container_logs=None,
            system_metrics=metrics
        )
        
        if analysis_result.get("status") != "success":
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "error": analysis_result.get("message", "AI analysis failed"),
                    "fault": fault
                }
            )
        
        # Determine if auto-healing is possible
        analysis = analysis_result.get("analysis", {})
        solution = analysis.get("solution", "")
        confidence = analysis.get("confidence", 0)
        
        # Check if solution contains executable commands that can be auto-healed
        auto_healable = False
        healing_steps = []
        
        if solution and confidence >= 50:  # Minimum confidence threshold
            # Check for common auto-healable actions
            solution_lower = solution.lower()
            auto_healable_keywords = [
                "restart", "restart service", "systemctl restart", "service restart",
                "clear cache", "free disk", "clean", "kill process", "kill -9",
                "reload", "reload config", "systemctl reload", "systemctl start",
                "systemctl stop", "systemctl enable", "systemctl disable"
            ]
            
            if any(keyword in solution_lower for keyword in auto_healable_keywords):
                auto_healable = True
                # Extract healing steps from solution - handle various formats
                lines = solution.split('\n')
                current_step = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_step:
                            healing_steps.append(current_step)
                            current_step = ""
                        continue
                    
                    # Check for step indicators
                    is_step = False
                    step_text = line
                    
                    # Remove common step prefixes
                    if line.startswith('-') or line.startswith('*') or line.startswith('•'):
                        step_text = line[1:].strip()
                        is_step = True
                    elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or \
                         line.startswith('4.') or line.startswith('5.') or line.startswith('6.') or \
                         line.startswith('7.') or line.startswith('8.') or line.startswith('9.'):
                        step_text = line.split('.', 1)[1].strip() if '.' in line else line
                        is_step = True
                    elif line[0].isdigit() and len(line) > 1 and line[1] in ['.', ')', '-']:
                        step_text = line.split(line[1], 1)[1].strip() if len(line) > 2 else line[2:].strip()
                        is_step = True
                    elif any(keyword in line.lower() for keyword in auto_healable_keywords):
                        is_step = True
                    
                    if is_step and step_text:
                        # Clean up the step text
                        step_text = step_text.strip()
                        if step_text and step_text not in healing_steps:
                            healing_steps.append(step_text)
                
                # If no structured steps found, try to extract from full solution
                if not healing_steps and solution:
                    # Look for command patterns
                    import re
                    commands = re.findall(r'(?:sudo\s+)?(?:systemctl|service|kill|restart|clear|clean|reload)\s+[^\n]+', solution, re.IGNORECASE)
                    if commands:
                        healing_steps = [cmd.strip() for cmd in commands[:10]]  # Limit to 10 steps
                    elif len(solution) < 500:  # If solution is short, use it as a single step
                        healing_steps = [solution]
        
        result = {
            "success": True,
            "fault": fault,
            "analysis": {
                "root_cause": analysis.get("root_cause", ""),
                "why": analysis.get("why", ""),
                "solution": solution,
                "prevention": analysis.get("prevention", ""),
                "confidence": confidence,
                "full_analysis": analysis.get("full_analysis", "")
            },
            "auto_healable": auto_healable,
            "healing_steps": healing_steps if auto_healable else [],
            "manual_instructions": solution if not auto_healable else "",
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Error analyzing fault with AI: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Internal server error: {str(e)}"}
        )

@app.post("/api/cloud/faults/{fault_id}/analyze-and-heal")
async def analyze_and_heal_fault(fault_id: int):
    """Analyze fault with AI and attempt automatic healing"""
    try:
        if not fault_detector:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Fault detector not initialized"}
            )
        
        if not auto_healer:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Auto-healer not initialized"}
            )
        
        faults = fault_detector.get_detected_faults(limit=100)
        if fault_id >= len(faults):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Fault not found"}
            )
        
        fault = faults[fault_id]
        
        # First, get AI analysis
        analysis_result = None
        if gemini_analyzer:
            try:
                metrics = get_system_metrics()
            except:
                metrics = None
            
            analysis_result = gemini_analyzer.analyze_cloud_fault(
                fault,
                container_logs=None,
                system_metrics=metrics
            )
        
        # Attempt healing
        healing_result = None
        healing_success = False
        healing_error = None
        
        try:
            # Use AI-provided solution if available
            if analysis_result and analysis_result.get("status") == "success":
                # Pass AI analysis to auto-healer
                fault_with_analysis = fault.copy()
                fault_with_analysis["ai_analysis"] = analysis_result.get("analysis", {})
                healing_result = auto_healer.heal_cloud_fault(fault_with_analysis)
            else:
                # Fallback to standard healing
                healing_result = auto_healer.heal_cloud_fault(fault)
            
            if healing_result:
                healing_success = healing_result.get("success", False) if isinstance(healing_result, dict) else False
                if not healing_success:
                    healing_error = healing_result.get("error", "Healing failed") if isinstance(healing_result, dict) else "Unknown error"
        except Exception as e:
            logger.error(f"Error during healing: {e}")
            healing_error = str(e)
        
        # Prepare response
        response = {
            "success": True,
            "fault": fault,
            "healing_attempted": True,
            "healing_success": healing_success,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add AI analysis if available
        if analysis_result and analysis_result.get("status") == "success":
            analysis = analysis_result.get("analysis", {})
            response["analysis"] = {
                "root_cause": analysis.get("root_cause", ""),
                "solution": analysis.get("solution", ""),
                "confidence": analysis.get("confidence", 0),
                "full_analysis": analysis.get("full_analysis", "")
            }
        
        # Add healing result
        if healing_result:
            response["healing_result"] = healing_result
            if isinstance(healing_result, dict):
                response["healing_steps"] = healing_result.get("actions", [])
                response["healing_status"] = healing_result.get("status", "unknown")
        
        # Add error if healing failed
        if not healing_success:
            response["healing_error"] = healing_error
            # Provide manual instructions from AI analysis
            if analysis_result and analysis_result.get("status") == "success":
                analysis = analysis_result.get("analysis", {})
                response["manual_instructions"] = analysis.get("solution", "")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in analyze-and-heal: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/cloud/faults/{fault_id}/heal")
async def heal_fault(fault_id: int, request: Request = None):
    """Manually trigger healing for a specific fault (with optional AI analysis)"""
    try:
        use_ai_analysis = False
        if request:
            try:
                body = await request.json()
                use_ai_analysis = body.get("use_ai_analysis", False)
            except:
                pass
        
        if not auto_healer or not fault_detector:
            return JSONResponse(
                status_code=503,
                content={"success": False, "error": "Auto-healer or fault detector not initialized"}
            )
        
        faults = fault_detector.get_detected_faults(limit=100)
        if fault_id >= len(faults):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Fault not found"}
            )
        
        fault = faults[fault_id]
        
        # Get AI analysis if requested
        ai_analysis = None
        if use_ai_analysis and gemini_analyzer:
            try:
                metrics = get_system_metrics()
            except:
                metrics = None
            
            analysis_result = gemini_analyzer.analyze_cloud_fault(
                fault,
                container_logs=None,
                system_metrics=metrics
            )
            
            if analysis_result.get("status") == "success":
                ai_analysis = analysis_result.get("analysis", {})
                fault["ai_analysis"] = ai_analysis
        
        # Attempt healing
        result = auto_healer.heal_cloud_fault(fault)
        
        response = {
            "success": True,
            "healing_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        if ai_analysis:
            response["ai_analysis"] = {
                "root_cause": ai_analysis.get("root_cause", ""),
                "solution": ai_analysis.get("solution", ""),
                "confidence": ai_analysis.get("confidence", 0)
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error healing fault: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/cloud/faults/cleanup")
async def cleanup_injected_faults():
    """Clean up all injected faults"""
    try:
        if not fault_injector:
            return {"success": False, "error": "Fault injector not initialized"}
        
        success, message = fault_injector.cleanup_injected_faults()
        return {
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning up faults: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HEALING_DASHBOARD_PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)

