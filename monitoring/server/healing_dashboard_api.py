"""
Healing Bot Dashboard API
Comprehensive backend for real-time system monitoring and management
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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
from typing import List, Dict, Any
from collections import defaultdict, Counter
import logging
import re
import requests
from pathlib import Path
import signal

# Initialize FastAPI app
app = FastAPI(title="Healing Bot Dashboard API")

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

# Global configuration
CONFIG = {
    "auto_restart": True,
    "cpu_threshold": 90.0,
    "memory_threshold": 85.0,
    "disk_threshold": 80.0,
    "discord_webhook": os.getenv("DISCORD_WEBHOOK", ""),
    "services_to_monitor": ["nginx", "mysql", "ssh", "docker", "postgresql"],
}

# Service status cache
service_cache = {}
last_cleanup_time = None
ssh_attempts = defaultdict(list)
blocked_ips = set()
command_history = []
log_buffer = []

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

def block_ip(ip: str):
    """Block an IP address using iptables"""
    if ip in blocked_ips:
        return
    
    try:
        subprocess.run(
            ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
            timeout=5
        )
        blocked_ips.add(ip)
        logger.warning(f"Blocked IP: {ip}")
        send_discord_alert(f"🚫 Blocked Suspicious IP: {ip}")
    except Exception as e:
        logger.error(f"Error blocking IP {ip}: {e}")

def unblock_ip(ip: str):
    """Unblock an IP address"""
    if ip not in blocked_ips:
        return
    
    try:
        subprocess.run(
            ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
            capture_output=True,
            timeout=5
        )
        blocked_ips.remove(ip)
        logger.info(f"Unblocked IP: {ip}")
    except Exception as e:
        logger.error(f"Error unblocking IP {ip}: {e}")

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
# Discord Integration
# ============================================================================

def send_discord_alert(message: str, severity: str = "info"):
    """Send alert to Discord"""
    if not CONFIG["discord_webhook"]:
        return
    
    try:
        emoji_map = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        color_map = {
            "info": 3447003,
            "success": 3066993,
            "warning": 16776960,
            "error": 15158332,
            "critical": 10038562
        }
        
        payload = {
            "embeds": [{
                "title": f"{emoji_map.get(severity, 'ℹ️')} Healing Bot Alert",
                "description": message,
                "color": color_map.get(severity, 3447003),
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        requests.post(CONFIG["discord_webhook"], json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Error sending Discord alert: {e}")

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
    """Start background tasks"""
    asyncio.create_task(monitoring_loop())
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
        CONFIG["discord_webhook"] = webhook
    
    send_discord_alert("Test notification from Healing Bot Dashboard", "info")
    return {"success": True}

@app.post("/api/discord/configure")
async def configure_discord(data: dict):
    """Configure Discord webhook"""
    CONFIG["discord_webhook"] = data.get("webhook", "")
    return {"success": True}

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HEALING_DASHBOARD_PORT", 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)

