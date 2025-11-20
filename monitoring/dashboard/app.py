"""
Unified Healing Bot Dashboard API
Combines ML Model Monitoring + System Health Management
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import psutil
import numpy as np
import subprocess
import os
import sys
import re
import signal
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import deque, defaultdict
from pathlib import Path
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Healing Bot Dashboard")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Prometheus metrics
dashboard_connections_total = Counter('dashboard_connections_total', 'Total dashboard connections')
dashboard_websocket_messages_total = Counter('dashboard_websocket_messages_total', 'Total WebSocket messages')
dashboard_attack_simulations_total = Counter('dashboard_attack_simulations_total', 'Total attack simulations')
dashboard_response_time_seconds = Histogram('dashboard_response_time_seconds', 'Dashboard response time')

# Global configuration
CONFIG = {
    "auto_restart": True,
    "cpu_threshold": 90.0,
    "memory_threshold": 85.0,
    "disk_threshold": 80.0,
    "discord_webhook": os.getenv("DISCORD_WEBHOOK") or os.getenv("DISCORD_WEBHOOK_URL", ""),
    "services_to_monitor": ["nginx", "mysql", "ssh", "docker", "postgresql"],
}

# ML Model metrics history
ml_metrics_history = {
    'timestamps': deque(maxlen=100),
    'accuracy': deque(maxlen=100),
    'precision': deque(maxlen=100),
    'recall': deque(maxlen=100),
    'f1_score': deque(maxlen=100),
    'prediction_time': deque(maxlen=100),
    'throughput': deque(maxlen=100)
}

# System metrics history
system_metrics_history = {
    'timestamps': deque(maxlen=100),
    'cpu_usage': deque(maxlen=100),
    'memory_usage': deque(maxlen=100),
    'disk_usage': deque(maxlen=100),
    'network_in': deque(maxlen=100),
    'network_out': deque(maxlen=100)
}

# Attack detection statistics
attack_stats = {
    'total_detections': 0,
    'ddos_attacks': 0,
    'false_positives': 0,
    'false_negatives': 0,
    'attack_types': defaultdict(int),
    'top_source_ips': defaultdict(int),
    'hourly_attacks': defaultdict(int)
}

# IP blocking statistics
blocking_stats = {
    'total_blocked': 0,
    'currently_blocked': 0,
    'auto_blocked': 0,
    'manual_blocked': 0,
    'unblocked': 0,
    'recent_blocks_24h': 0,
    'blocking_rate': 0.0
}

# Service cache, SSH attempts, blocked IPs
service_cache = {}
last_cleanup_time = None
ssh_attempts = defaultdict(list)
blocked_ips = set()
command_history = []
log_buffer = []

# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        dashboard_connections_total.inc()
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                dashboard_websocket_messages_total.inc()
            except:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# ============================================================================
# ML Model Monitoring
# ============================================================================

class MLModelMonitor:
    def __init__(self):
        self.model_url = os.getenv("MODEL_URL", "http://localhost:8080")
        self.monitoring_server_url = os.getenv("MONITORING_SERVER_URL", "http://localhost:5000")
        self.network_analyzer_url = os.getenv("NETWORK_ANALYZER_URL", "http://localhost:8000")
        self.last_prediction_time = 0
        self.prediction_count = 0
        self.start_time = time.time()

    async def get_model_health(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.model_url}/health", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    async def simulate_model_metrics(self) -> Dict[str, Any]:
        current_time = time.time()
        
        # Simulate realistic ML metrics
        base_accuracy = 0.95
        accuracy_variation = np.random.normal(0, 0.02)
        accuracy = max(0.8, min(0.99, base_accuracy + accuracy_variation))
        
        precision = max(0.85, min(0.98, accuracy + np.random.normal(0, 0.01)))
        recall = max(0.88, min(0.97, accuracy + np.random.normal(0, 0.015)))
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        prediction_time = np.random.exponential(50) + 10
        
        if current_time - self.last_prediction_time > 0:
            throughput = 1 / (current_time - self.last_prediction_time)
        else:
            throughput = 0
        
        self.last_prediction_time = current_time
        self.prediction_count += 1
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'prediction_time_ms': prediction_time,
            'throughput': min(throughput, 100),
            'total_predictions': self.prediction_count,
            'uptime_hours': (current_time - self.start_time) / 3600
        }

    async def get_attack_statistics(self) -> Dict[str, Any]:
        current_hour = datetime.now().hour
        
        # Simulate attack detection
        if np.random.random() < 0.1:
            attack_types = ['HTTP Flood', 'SYN Flood', 'UDP Flood', 'ICMP Flood', 'Slowloris']
            attack_type = np.random.choice(attack_types)
            attack_stats['attack_types'][attack_type] += 1
            attack_stats['total_detections'] += 1
            attack_stats['ddos_attacks'] += 1
            attack_stats['hourly_attacks'][current_hour] += 1
            
            source_ip = f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}"
            attack_stats['top_source_ips'][source_ip] += 1
        
        return {
            'total_detections': attack_stats['total_detections'],
            'ddos_attacks': attack_stats['ddos_attacks'],
            'false_positives': attack_stats['false_positives'],
            'false_negatives': attack_stats['false_negatives'],
            'attack_types': dict(attack_stats['attack_types']),
            'top_source_ips': dict(list(attack_stats['top_source_ips'].items())[:10]),
            'hourly_attacks': dict(attack_stats['hourly_attacks']),
            'detection_rate': attack_stats['total_detections'] / max(1, self.prediction_count) * 100
        }

    async def get_blocking_statistics(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.network_analyzer_url}/blocked-ips/stats", timeout=5)
            if response.status_code == 200:
                return response.json().get('statistics', {})
        except:
            pass
        
        return {
            'total_blocked': blocking_stats['total_blocked'],
            'currently_blocked': blocking_stats['currently_blocked'],
            'auto_blocked': blocking_stats['auto_blocked'],
            'manual_blocked': blocking_stats['manual_blocked'],
            'unblocked': blocking_stats['unblocked'],
            'recent_blocks_24h': blocking_stats['recent_blocks_24h'],
            'blocking_rate': blocking_stats['blocking_rate']
        }

    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        try:
            response = requests.get(f"{self.network_analyzer_url}/blocked-ips", timeout=5)
            if response.status_code == 200:
                return response.json().get('blocked_ips', [])
        except:
            pass
        return []

ml_monitor = MLModelMonitor()

# ============================================================================
# System Monitoring
# ============================================================================

def get_system_metrics() -> Dict[str, Any]:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        return {
            "cpu": cpu_percent,
            "memory": memory.percent,
            "disk": disk.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "network_in_mbps": net_io.bytes_recv / (1024**2),
            "network_out_mbps": net_io.bytes_sent / (1024**2),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {}

# ============================================================================
# Service Management
# ============================================================================

def check_service_status(service_name: str) -> Dict[str, Any]:
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
    except:
        return {"name": service_name, "status": "unknown", "active": False}

def get_all_services_status() -> List[Dict[str, Any]]:
    services = []
    for service in CONFIG["services_to_monitor"]:
        status = check_service_status(service)
        services.append(status)
    return services

def restart_service(service_name: str) -> bool:
    try:
        logger.info(f"Restarting service: {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully restarted {service_name}")
            log_event("info", f"Service {service_name} restarted")
            send_discord_alert(f"✅ Service Restarted: {service_name}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error restarting {service_name}: {e}")
        return False

# ============================================================================
# Process Management
# ============================================================================

def get_top_processes(limit: int = 10) -> List[Dict[str, Any]]:
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
        
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        return []

def kill_process(pid: int) -> bool:
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        proc.terminate()
        proc.wait(timeout=3)
        
        logger.info(f"Killed process {proc_name} (PID: {pid})")
        log_event("warning", f"Killed process: {proc_name} (PID: {pid})")
        send_discord_alert(f"💀 Killed Process: {proc_name} (PID: {pid})")
        return True
    except psutil.TimeoutExpired:
        try:
            proc.kill()
            return True
        except:
            return False
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}")
        return False

# ============================================================================
# SSH Intrusion Detection
# ============================================================================

def parse_ssh_logs() -> List[Dict[str, Any]]:
    ssh_events = []
    try:
        if os.path.exists("/var/log/auth.log"):
            with open("/var/log/auth.log", "r") as f:
                lines = f.readlines()[-1000:]
                
                for line in lines:
                    if "Failed password" in line:
                        match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            ip = match.group(1)
                            timestamp = line.split()[0:3]
                            ssh_attempts[ip].append(datetime.now())
                            
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

def block_ip(ip: str):
    if ip in blocked_ips:
        return
    try:
        subprocess.run(
            ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
            timeout=5
        )
        blocked_ips.add(ip)
        blocking_stats['total_blocked'] += 1
        blocking_stats['currently_blocked'] += 1
        logger.warning(f"Blocked IP: {ip}")
        send_discord_alert(f"🚫 Blocked IP: {ip}")
    except Exception as e:
        logger.error(f"Error blocking IP {ip}: {e}")

def unblock_ip(ip: str):
    if ip not in blocked_ips:
        return
    try:
        subprocess.run(
            ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
            timeout=5
        )
        blocked_ips.remove(ip)
        blocking_stats['currently_blocked'] -= 1
        blocking_stats['unblocked'] += 1
        logger.info(f"Unblocked IP: {ip}")
    except Exception as e:
        logger.error(f"Error unblocking IP {ip}: {e}")

# ============================================================================
# Disk Cleanup
# ============================================================================

def run_disk_cleanup() -> Dict[str, Any]:
    """Run disk cleanup operations (rate limited to once per hour)"""
    global last_cleanup_time
    
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
        
        final_usage = psutil.disk_usage('/')
        freed_space = (initial_usage.used - final_usage.used) / (1024 * 1024)
        
        last_cleanup_time = datetime.now()
        
        logger.info(f"Disk cleanup freed {freed_space:.2f} MB")
        log_event("success", f"Disk cleanup freed {freed_space:.2f} MB")
        send_discord_alert(f"🧹 Cleanup Complete: Freed {freed_space:.2f} MB")
        
        return {
            "success": True,
            "freed_space": round(freed_space, 2),
            "timestamp": last_cleanup_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error during disk cleanup: {e}")
        return {"success": False, "error": str(e)}

# ============================================================================
# Discord Integration
# ============================================================================

def send_discord_alert(message: str, severity: str = "info"):
    if not CONFIG["discord_webhook"]:
        logger.warning("Discord webhook not configured. Notification not sent.")
        return False
    
    try:
        emoji_map = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        color_map = {"info": 3447003, "success": 3066993, "warning": 16776960, "error": 15158332, "critical": 10038562}
        
        payload = {
            "embeds": [{
                "title": f"{emoji_map.get(severity, 'ℹ️')} Healing Bot Alert",
                "description": message,
                "color": color_map.get(severity, 3447003),
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
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
        if response.status_code in [200, 201, 204]:
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

# ============================================================================
# Event Logging
# ============================================================================

def log_event(level: str, message: str):
    log_buffer.append({
        "level": level,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    if len(log_buffer) > 1000:
        log_buffer.pop(0)

# ============================================================================
# Background Monitoring Loop
# ============================================================================

async def monitoring_loop():
    while True:
        try:
            # Get system metrics
            metrics = get_system_metrics()
            ml_metrics = await ml_monitor.simulate_model_metrics()
            attack_stats_data = await ml_monitor.get_attack_statistics()
            blocking_stats_data = await ml_monitor.get_blocking_statistics()
            
            # Update histories
            current_time = datetime.now()
            ml_metrics_history['timestamps'].append(current_time.isoformat())
            ml_metrics_history['accuracy'].append(ml_metrics['accuracy'])
            ml_metrics_history['precision'].append(ml_metrics['precision'])
            ml_metrics_history['recall'].append(ml_metrics['recall'])
            ml_metrics_history['f1_score'].append(ml_metrics['f1_score'])
            ml_metrics_history['prediction_time'].append(ml_metrics['prediction_time_ms'])
            ml_metrics_history['throughput'].append(ml_metrics['throughput'])
            
            system_metrics_history['timestamps'].append(current_time.isoformat())
            system_metrics_history['cpu_usage'].append(metrics.get('cpu', 0))
            system_metrics_history['memory_usage'].append(metrics.get('memory', 0))
            system_metrics_history['disk_usage'].append(metrics.get('disk', 0))
            system_metrics_history['network_in'].append(metrics.get('network_in_mbps', 0))
            system_metrics_history['network_out'].append(metrics.get('network_out_mbps', 0))
            
            # Check services if auto-restart enabled
            if CONFIG["auto_restart"]:
                services = get_all_services_status()
                for service in services:
                    if not service["active"]:
                        restart_service(service["name"])
            
            # Check disk usage (only run cleanup once per hour)
            if metrics.get('disk', 0) > CONFIG["disk_threshold"]:
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
            
            # Broadcast unified data
            dashboard_data = {
                'timestamp': current_time.isoformat(),
                'ml_metrics': ml_metrics,
                'system_metrics': metrics,
                'attack_statistics': attack_stats_data,
                'blocking_statistics': blocking_stats_data,
                'ml_history': {
                    'timestamps': list(ml_metrics_history['timestamps']),
                    'accuracy': list(ml_metrics_history['accuracy']),
                    'precision': list(ml_metrics_history['precision']),
                    'recall': list(ml_metrics_history['recall']),
                    'f1_score': list(ml_metrics_history['f1_score'])
                },
                'system_history': {
                    'timestamps': list(system_metrics_history['timestamps']),
                    'cpu_usage': list(system_metrics_history['cpu_usage']),
                    'memory_usage': list(system_metrics_history['memory_usage']),
                    'disk_usage': list(system_metrics_history['disk_usage'])
                }
            }
            
            await manager.broadcast(dashboard_data)
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        await asyncio.sleep(2)

# ============================================================================
# API Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitoring_loop())
    logger.info("Unified Dashboard API started")

@app.get("/")
async def root():
    dashboard_path = Path(__file__).parent / "static" / "dashboard.html"
    with open(dashboard_path, "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/metrics")
async def get_metrics():
    return get_system_metrics()

@app.get("/api/metrics/ml")
async def get_ml_metrics():
    return await ml_monitor.simulate_model_metrics()

@app.get("/api/metrics/system")
async def get_system_metrics_endpoint():
    return get_system_metrics()

@app.get("/api/metrics/attacks")
async def get_attack_metrics():
    return await ml_monitor.get_attack_statistics()

@app.get("/api/history/ml")
async def get_ml_history():
    return {
        'timestamps': list(ml_metrics_history['timestamps']),
        'accuracy': list(ml_metrics_history['accuracy']),
        'precision': list(ml_metrics_history['precision']),
        'recall': list(ml_metrics_history['recall']),
        'f1_score': list(ml_metrics_history['f1_score']),
        'prediction_time': list(ml_metrics_history['prediction_time']),
        'throughput': list(ml_metrics_history['throughput'])
    }

@app.get("/api/history/system")
async def get_system_history():
    return {
        'timestamps': list(system_metrics_history['timestamps']),
        'cpu_usage': list(system_metrics_history['cpu_usage']),
        'memory_usage': list(system_metrics_history['memory_usage']),
        'disk_usage': list(system_metrics_history['disk_usage']),
        'network_in': list(system_metrics_history['network_in']),
        'network_out': list(system_metrics_history['network_out'])
    }

@app.get("/api/blocking/stats")
async def get_blocking_stats():
    return await ml_monitor.get_blocking_statistics()

@app.get("/api/blocking/ips")
async def get_blocked_ips_list():
    return await ml_monitor.get_blocked_ips()

@app.post("/api/blocking/block")
async def block_ip_endpoint(request: dict):
    try:
        ip = request.get('ip')
        if not ip:
            return {"error": "IP required"}
        block_ip(ip)
        return {"status": "success", "ip": ip}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/blocking/unblock")
async def unblock_ip_endpoint(request: dict):
    try:
        ip = request.get('ip')
        if not ip:
            return {"error": "IP required"}
        unblock_ip(ip)
        return {"status": "success", "ip": ip}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/services")
async def get_services():
    return {"services": get_all_services_status()}

@app.post("/api/services/{service_name}/restart")
async def restart_service_endpoint(service_name: str):
    success = restart_service(service_name)
    return {"success": success, "service": service_name}

@app.get("/api/processes/top")
async def get_top_processes_endpoint(limit: int = 10):
    return get_top_processes(limit)

@app.post("/api/processes/kill")
async def kill_process_endpoint(data: dict):
    pid = data.get("pid")
    if not pid:
        return {"error": "PID required"}
    success = kill_process(pid)
    return {"success": success, "pid": pid}

@app.get("/api/ssh/attempts")
async def get_ssh_attempts():
    return {"attempts": parse_ssh_logs()}

@app.post("/api/ssh/block")
async def block_ip_ssh(data: dict):
    ip = data.get("ip")
    if not ip:
        return {"error": "IP required"}
    block_ip(ip)
    return {"success": True, "ip": ip}

@app.post("/api/ssh/unblock")
async def unblock_ip_ssh(data: dict):
    ip = data.get("ip")
    if not ip:
        return {"error": "IP required"}
    unblock_ip(ip)
    return {"success": True, "ip": ip}

@app.get("/api/disk/status")
async def get_disk_status():
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
    return run_disk_cleanup()

@app.post("/api/discord/test")
async def test_discord_endpoint(data: dict):
    webhook = data.get("webhook")
    if webhook:
        CONFIG["discord_webhook"] = webhook
    
    if not CONFIG["discord_webhook"]:
        return {"success": False, "error": "Discord webhook not configured"}
    
    success = send_discord_alert("Test notification from Healing Bot", "info")
    if success:
        return {"success": True, "message": "Test notification sent successfully"}
    else:
        return {"success": False, "error": "Failed to send test notification. Check server logs for details."}

@app.post("/api/discord/configure")
async def configure_discord(data: dict):
    CONFIG["discord_webhook"] = data.get("webhook", "")
    return {"success": True}

@app.get("/api/logs")
async def get_logs(limit: int = 100):
    return {"logs": log_buffer[-limit:]}

@app.post("/api/cli/execute")
async def execute_cli_endpoint(data: dict):
    command = data.get("command", "")
    if not command:
        return {"error": "No command"}
    
    command_history.append({"command": command, "timestamp": datetime.now().isoformat()})
    
    allowed_commands = ["help", "status", "services", "processes", "disk", "logs", "restart"]
    cmd_parts = command.split()
    
    if not cmd_parts or cmd_parts[0] not in allowed_commands:
        return {"error": "Command not allowed"}
    
    try:
        if cmd_parts[0] == "help":
            output = "Available: help, status, services, processes, disk, logs, restart <service>"
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
    return CONFIG

@app.post("/api/config")
async def update_config(data: dict):
    CONFIG.update(data)
    return {"success": True, "config": CONFIG}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("DASHBOARD_PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)

