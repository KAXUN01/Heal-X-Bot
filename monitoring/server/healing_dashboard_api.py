"""
Healing Bot Dashboard API
Comprehensive backend for real-time system monitoring and management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
env_path_abs = env_path.resolve()
# Convert Path to string for load_dotenv and override existing env vars
load_dotenv(dotenv_path=str(env_path_abs), override=True)
from system_log_collector import initialize_system_log_collector, get_system_log_collector
from centralized_logger import initialize_centralized_logging, centralized_logger
from gemini_log_analyzer import initialize_gemini_analyzer, gemini_analyzer
from critical_services_monitor import initialize_critical_services_monitor, get_critical_services_monitor
from fluent_bit_reader import initialize_fluent_bit_reader, fluent_bit_reader

# Initialize FastAPI app
app = FastAPI(title="Healing Bot Dashboard API")

# Initialize blocked IPs database
blocked_ips_db = BlockedIPsDatabase("monitoring/server/data/blocked_ips.db")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
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
    
    return {
        "auto_restart": True,
        "cpu_threshold": 90.0,
        "memory_threshold": 85.0,
        "disk_threshold": 80.0,
        "discord_webhook": discord_webhook,
        "services_to_monitor": ["nginx", "mysql", "ssh", "docker", "postgresql"],
        "model_service_url": os.getenv("MODEL_SERVICE_URL", "http://localhost:8080"),
    }

CONFIG = load_config()

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
ssh_attempts = defaultdict(list)
blocked_ips = set()
command_history = []
log_buffer = []

# Track notified critical errors to avoid duplicates
notified_critical_errors = set()  # Set of (timestamp, service, message_hash) tuples

# Track last sent warnings and time-to-failure for Discord notifications
_last_sent_warnings = set()  # Set of warning types that were sent
_last_sent_warning_count = 0  # Last warning count sent
_last_sent_time_to_failure = None  # Last time-to-failure value sent
_last_warning_notification_time = None  # Last time warnings were sent
_last_time_to_failure_notification_time = None  # Last time time-to-failure was sent

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
        is_active = result.stdout.strip() == "active"
        
        return {
            "name": service_name,
            "status": "running" if is_active else "stopped",
            "active": is_active
        }
    except subprocess.TimeoutExpired:
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

def restart_service(service_name: str) -> bool:
    """Restart a failed service"""
    try:
        logger.info(f"Attempting to restart service: {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully restarted {service_name}")
            log_event("info", f"Service {service_name} restarted successfully")
            send_discord_alert(f"✅ Service Restarted: {service_name}")
            return True
        else:
            logger.error(f"Failed to restart {service_name}: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error restarting service {service_name}: {e}")
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
        send_discord_alert(f"💀 Killed Resource Hog: {proc_name} (PID: {pid})")
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
                if pinfo['cpu_percent'] > CONFIG['cpu_threshold']:
                    logger.warning(f"CPU hog detected: {pinfo['name']} ({pinfo['cpu_percent']}%)")
                    send_discord_alert(f"⚠️ CPU Hog Detected: {pinfo['name']} using {pinfo['cpu_percent']}% CPU")
                
                if pinfo['memory_percent'] > CONFIG['memory_threshold']:
                    logger.warning(f"Memory hog detected: {pinfo['name']} ({pinfo['memory_percent']}%)")
                    send_discord_alert(f"⚠️ Memory Hog Detected: {pinfo['name']} using {pinfo['memory_percent']}% RAM")
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
            if iptables_success:
                send_discord_alert(f"🚫 Blocked IP: {ip}\nThreat Level: {threat_level}\nAttacks: {attack_count}\nFirewall: Active")
            else:
                send_discord_alert(f"🚫 Blocked IP (Database Only): {ip}\nThreat Level: {threat_level}\nAttacks: {attack_count}\nNote: Manual iptables configuration needed")
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
    """Run disk cleanup operations"""
    global last_cleanup_time
    
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
        
        logger.info(f"Disk cleanup completed. Freed {freed_space:.2f} MB")
        log_event("success", f"Disk cleanup freed {freed_space:.2f} MB")
        send_discord_alert(f"🧹 Disk Cleanup Complete: Freed {freed_space:.2f} MB")
        
        return {
            "success": True,
            "freed_space": round(freed_space, 2),
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

def send_discord_alert(message: str, severity: str = "info", embed_data: Dict[str, Any] = None):
    """Send alert to Discord with optional detailed embed data"""
    if not CONFIG["discord_webhook"]:
        logger.warning("Discord webhook not configured. Notification not sent.")
        return False
    
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
                for service in services:
                    if not service["active"]:
                        restart_service(service["name"])
            
            # Check resource hogs
            auto_detect_resource_hogs()
            
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > CONFIG["disk_threshold"]:
                run_disk_cleanup()
            
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
    asyncio.create_task(monitoring_loop())
    
    # Initialize cloud simulation components
    initialize_cloud_components()
    
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
    dashboard_path = Path(__file__).parent.parent / "dashboard" / "static" / "healing-dashboard.html"
    with open(dashboard_path, "r") as f:
        return HTMLResponse(content=f.read())

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
    """Get all services status"""
    return {"services": get_all_services_status()}

@app.post("/api/services/{service_name}/restart")
async def restart_service_endpoint(service_name: str):
    """Restart a specific service"""
    success = restart_service(service_name)
    return {"success": success, "service": service_name}

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
        "last_cleanup": last_cleanup_time.isoformat() if last_cleanup_time else None
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
                # Create unique identifier for this error
                timestamp = issue.get('timestamp', '')
                service = issue.get('service', 'unknown')
                message = issue.get('message', '')
                message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
                error_id = (timestamp, service, message_hash)
                
                # Check if we've already notified about this error
                if error_id not in notified_critical_errors:
                    # Mark as notified
                    notified_critical_errors.add(error_id)
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
        
        # Clean up old notified errors (keep last 1000 to prevent memory growth)
        if len(notified_critical_errors) > 1000:
            # Keep only the most recent 500
            notified_critical_errors.clear()
            # Re-add current issues
            for issue in issues[:500]:
                timestamp = issue.get('timestamp', '')
                service = issue.get('service', 'unknown')
                message = issue.get('message', '')
                message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
                error_id = (timestamp, service, message_hash)
                notified_critical_errors.add(error_id)
        
        if new_critical_count > 0:
            logger.info(f"Sent Discord notifications for {new_critical_count} new CRITICAL error(s)")
        
        return {
            "status": "success",
            "issues": issues,
            "count": len(issues)
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

# Gemini AI Log Analysis Endpoints
@app.post("/api/gemini/analyze-log")
async def analyze_single_log(data: dict):
    """Analyze a single log entry using Gemini AI"""
    try:
        # Use the global gemini_analyzer from the module
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        if not _gemini_analyzer:
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized. Check GEMINI_API_KEY"
            }
        
        log_entry = data
        
        if not log_entry:
            return {
                "status": "error",
                "message": "No log entry provided"
            }
        
        # Analyze the log
        analysis = _gemini_analyzer.analyze_error_log(log_entry)
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing log: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/gemini/analyze-pattern")
async def analyze_log_pattern(data: dict):
    """Analyze multiple logs for patterns using Gemini AI"""
    try:
        from gemini_log_analyzer import gemini_analyzer as _gemini_analyzer
        if not _gemini_analyzer:
            return {
                "status": "error",
                "message": "Gemini analyzer not initialized"
            }
        
        log_entries = data.get("logs", [])
        limit = data.get("limit", 10)
        
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
async def execute_cli_endpoint(data: dict):
    """Execute CLI command"""
    command = data.get("command", "")
    
    if not command:
        return {"error": "No command provided"}
    
    # Add to history
    command_history.append({
        "command": command,
        "timestamp": datetime.now().isoformat()
    })
    
    # Security: whitelist allowed commands
    allowed_commands = ["help", "status", "services", "processes", "disk", "logs", "restart"]
    cmd_parts = command.split()
    
    if not cmd_parts or cmd_parts[0] not in allowed_commands:
        return {"error": "Command not allowed"}
    
    # Execute command
    try:
        if cmd_parts[0] == "help":
            output = """Available commands:
- help: Show this help
- status: Show system status
- services: List all services
- processes: Show top processes
- disk: Show disk usage
- logs: Show recent logs
- restart <service>: Restart a service"""
        
        elif cmd_parts[0] == "status":
            metrics = get_system_metrics()
            output = f"CPU: {metrics['cpu']}%\nMemory: {metrics['memory']}%\nDisk: {metrics['disk']}%"
        
        elif cmd_parts[0] == "services":
            services = get_all_services_status()
            output = "\n".join([f"{s['name']}: {s['status']}" for s in services])
        
        elif cmd_parts[0] == "processes":
            processes = get_top_processes(5)
            output = "\n".join([f"{p['name']} - CPU: {p['cpu']}%, MEM: {p['memory']}%" for p in processes])
        
        elif cmd_parts[0] == "disk":
            disk = psutil.disk_usage('/')
            output = f"Total: {disk.total // (1024**3)} GB\nUsed: {disk.used // (1024**3)} GB\nFree: {disk.free // (1024**3)} GB\nPercent: {disk.percent}%"
        
        elif cmd_parts[0] == "logs":
            output = "\n".join([f"[{log['level']}] {log['message']}" for log in log_buffer[-10:]])
        
        elif cmd_parts[0] == "restart" and len(cmd_parts) > 1:
            service = cmd_parts[1]
            success = restart_service(service)
            output = f"Service {service} {'restarted successfully' if success else 'failed to restart'}"
        
        else:
            output = "Invalid command"
        
        return {"output": output, "command": command}
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return CONFIG

@app.post("/api/config")
async def update_config(data: dict):
    """Update configuration"""
    CONFIG.update(data)
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
        model_path = Path(__file__).parent.parent.parent / "model" / "artifacts" / "latest" / "model_loader.py"
        if model_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("model_loader", model_path)
            model_loader = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(model_loader)
            return model_loader
        return None
    except Exception as e:
        logger.warning(f"Could not load predictive model: {e}")
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
async def block_ip_ddos(data: dict):
    """Block an IP address (DDoS endpoint)"""
    ip = data.get("ip")
    if not ip:
        raise HTTPException(status_code=400, detail="IP is required")
    
    attack_count = data.get("attack_count", 1)
    threat_level = data.get("threat_level", "Medium")
    attack_type = data.get("attack_type")
    reason = data.get("reason", f"Manual block via dashboard")
    blocked_by = data.get("blocked_by", "dashboard")
    
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
        auto_healer.start_monitoring(interval=60)
        
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
            return {"success": False, "error": "Fault detector not initialized"}
        
        faults = fault_detector.get_detected_faults(limit=limit)
        stats = fault_detector.get_fault_statistics()
        
        return {
            "success": True,
            "faults": faults,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting detected faults: {e}")
        return {"success": False, "error": str(e)}

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
            return {"success": False, "error": "Auto-healer not initialized"}
        
        history = auto_healer.get_healing_history(limit=limit)
        stats = auto_healer.get_healing_statistics()
        
        return {
            "success": True,
            "history": history,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting healing history: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/cloud/faults/{fault_id}/heal")
async def heal_fault(fault_id: int):
    """Manually trigger healing for a specific fault"""
    try:
        if not auto_healer or not fault_detector:
            return {"success": False, "error": "Auto-healer or fault detector not initialized"}
        
        faults = fault_detector.get_detected_faults(limit=100)
        if fault_id < len(faults):
            fault = faults[fault_id]
            result = auto_healer.heal_cloud_fault(fault)
            return {
                "success": True,
                "healing_result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "Fault not found"}
    except Exception as e:
        logger.error(f"Error healing fault: {e}")
        return {"success": False, "error": str(e)}

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

