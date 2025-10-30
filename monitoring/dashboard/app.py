"""
Real-time ML Model Performance Dashboard
Monitors DDoS detection model performance and system statistics
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
import asyncio
import json
import time
import psutil
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import requests
import threading
from collections import deque, defaultdict
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Model Performance Dashboard")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Prometheus metrics
dashboard_connections_total = Counter('dashboard_connections_total', 'Total number of dashboard connections')
dashboard_websocket_messages_total = Counter('dashboard_websocket_messages_total', 'Total number of WebSocket messages sent')
dashboard_attack_simulations_total = Counter('dashboard_attack_simulations_total', 'Total number of attack simulations')
dashboard_response_time_seconds = Histogram('dashboard_response_time_seconds', 'Dashboard response time in seconds')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Global variables for real-time data
connected_clients: List[WebSocket] = []
ml_metrics_history = {
    'timestamps': deque(maxlen=100),
    'accuracy': deque(maxlen=100),
    'precision': deque(maxlen=100),
    'recall': deque(maxlen=100),
    'f1_score': deque(maxlen=100),
    'prediction_time': deque(maxlen=100),
    'throughput': deque(maxlen=100)
}

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

class MLModelMonitor:
    """Monitor ML model performance and collect metrics"""
    
    def __init__(self):
        # Use localhost for native mode, model:8080 for Docker mode
        self.model_url = os.getenv("MODEL_URL", "http://localhost:8080")
        self.monitoring_server_url = os.getenv("MONITORING_SERVER_URL", "http://localhost:5000")
        self.last_prediction_time = 0
        self.prediction_count = 0
        self.start_time = time.time()
        
    async def get_model_health(self) -> Dict[str, Any]:
        """Get model health status"""
        try:
            response = requests.get(f"{self.model_url}/health", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "response_time": response.elapsed.total_seconds()}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    async def simulate_model_metrics(self) -> Dict[str, Any]:
        """Simulate ML model metrics (replace with actual model calls)"""
        current_time = time.time()
        
        # Simulate realistic ML metrics with some variation
        base_accuracy = 0.95
        accuracy_variation = np.random.normal(0, 0.02)
        accuracy = max(0.8, min(0.99, base_accuracy + accuracy_variation))
        
        precision = max(0.85, min(0.98, accuracy + np.random.normal(0, 0.01)))
        recall = max(0.88, min(0.97, accuracy + np.random.normal(0, 0.015)))
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        # Simulate prediction time (milliseconds)
        prediction_time = np.random.exponential(50) + 10  # 10-100ms typical range
        
        # Calculate throughput (predictions per second)
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
            'throughput': min(throughput, 100),  # Cap at 100 predictions/sec
            'total_predictions': self.prediction_count,
            'uptime_hours': (current_time - self.start_time) / 3600
        }
    
    async def get_attack_statistics(self) -> Dict[str, Any]:
        """Get attack detection statistics"""
        current_hour = datetime.now().hour
        
        # Simulate some attack detection activity
        if np.random.random() < 0.1:  # 10% chance of attack detection
            attack_types = ['HTTP Flood', 'SYN Flood', 'UDP Flood', 'ICMP Flood', 'Slowloris']
            attack_type = np.random.choice(attack_types)
            attack_stats['attack_types'][attack_type] += 1
            attack_stats['total_detections'] += 1
            attack_stats['ddos_attacks'] += 1
            attack_stats['hourly_attacks'][current_hour] += 1
            
            # Simulate source IP
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
        """Get IP blocking statistics from network analyzer"""
        try:
            # Try to get real data from network analyzer
            response = requests.get(f"{self.network_analyzer_url}/blocked-ips/stats", timeout=5)
            if response.status_code == 200:
                return response.json().get('statistics', {})
        except Exception as e:
            logger.warning(f"Could not fetch real blocking stats: {e}")
        
        # Fallback to simulated data
        return {
            'total_blocked': blocking_stats['total_blocked'],
            'currently_blocked': blocking_stats['currently_blocked'],
            'auto_blocked': blocking_stats['auto_blocked'],
            'manual_blocked': blocking_stats['manual_blocked'],
            'unblocked': blocking_stats['unblocked'],
            'recent_blocks_24h': blocking_stats['recent_blocks_24h'],
            'blocking_rate': blocking_stats['blocking_rate'],
            'attack_types': {},
            'threat_levels': {}
        }
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs from network analyzer"""
        try:
            response = requests.get(f"{self.network_analyzer_url}/blocked-ips", timeout=5)
            if response.status_code == 200:
                return response.json().get('blocked_ips', [])
        except Exception as e:
            logger.warning(f"Could not fetch blocked IPs: {e}")
        
        # Fallback to empty list
        return []

# Initialize monitor
ml_monitor = MLModelMonitor()

class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    
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
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                dashboard_websocket_messages_total.inc()
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

async def collect_system_metrics() -> Dict[str, Any]:
    """Collect system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        return {
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_usage': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'network_in_mbps': net_io.bytes_recv / (1024**2),
            'network_out_mbps': net_io.bytes_sent / (1024**2),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        return {}

async def update_metrics():
    """Update metrics and broadcast to clients"""
    while True:
        try:
            # Collect ML model metrics
            ml_metrics = await ml_monitor.simulate_model_metrics()
            attack_stats_data = await ml_monitor.get_attack_statistics()
            blocking_stats_data = await ml_monitor.get_blocking_statistics()
            blocked_ips_data = await ml_monitor.get_blocked_ips()
            system_metrics = await collect_system_metrics()
            
            # Update history
            current_time = datetime.now()
            ml_metrics_history['timestamps'].append(current_time.isoformat())
            ml_metrics_history['accuracy'].append(ml_metrics['accuracy'])
            ml_metrics_history['precision'].append(ml_metrics['precision'])
            ml_metrics_history['recall'].append(ml_metrics['recall'])
            ml_metrics_history['f1_score'].append(ml_metrics['f1_score'])
            ml_metrics_history['prediction_time'].append(ml_metrics['prediction_time_ms'])
            ml_metrics_history['throughput'].append(ml_metrics['throughput'])
            
            system_metrics_history['timestamps'].append(current_time.isoformat())
            system_metrics_history['cpu_usage'].append(system_metrics.get('cpu_usage', 0))
            system_metrics_history['memory_usage'].append(system_metrics.get('memory_usage', 0))
            system_metrics_history['disk_usage'].append(system_metrics.get('disk_usage', 0))
            system_metrics_history['network_in'].append(system_metrics.get('network_in_mbps', 0))
            system_metrics_history['network_out'].append(system_metrics.get('network_out_mbps', 0))
            
            # Prepare dashboard data
            dashboard_data = {
                'timestamp': current_time.isoformat(),
                'ml_metrics': ml_metrics,
                'attack_statistics': attack_stats_data,
                'blocking_statistics': blocking_stats_data,
                'blocked_ips': blocked_ips_data,
                'system_metrics': system_metrics,
                'ml_history': {
                    'timestamps': list(ml_metrics_history['timestamps']),
                    'accuracy': list(ml_metrics_history['accuracy']),
                    'precision': list(ml_metrics_history['precision']),
                    'recall': list(ml_metrics_history['recall']),
                    'f1_score': list(ml_metrics_history['f1_score']),
                    'prediction_time': list(ml_metrics_history['prediction_time']),
                    'throughput': list(ml_metrics_history['throughput'])
                },
                'system_history': {
                    'timestamps': list(system_metrics_history['timestamps']),
                    'cpu_usage': list(system_metrics_history['cpu_usage']),
                    'memory_usage': list(system_metrics_history['memory_usage']),
                    'disk_usage': list(system_metrics_history['disk_usage']),
                    'network_in': list(system_metrics_history['network_in']),
                    'network_out': list(system_metrics_history['network_out'])
                }
            }
            
            # Broadcast to all connected clients
            await manager.broadcast(dashboard_data)
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
        
        await asyncio.sleep(2)  # Update every 2 seconds

@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup"""
    asyncio.create_task(update_metrics())
    logger.info("Dashboard started with real-time metrics collection")

@app.get("/")
async def dashboard():
    """Serve the main dashboard page"""
    with open("static/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    dashboard_connections_total.inc()
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/model/health")
async def model_health():
    """Check ML model health"""
    return await ml_monitor.get_model_health()

@app.get("/api/metrics/ml")
async def get_ml_metrics():
    """Get current ML model metrics"""
    return await ml_monitor.simulate_model_metrics()

@app.get("/api/metrics/system")
async def get_system_metrics():
    """Get current system metrics"""
    return await collect_system_metrics()

@app.get("/api/metrics/attacks")
async def get_attack_metrics():
    """Get attack detection metrics"""
    return await ml_monitor.get_attack_statistics()

@app.get("/api/history/ml")
async def get_ml_history():
    """Get ML metrics history"""
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
    """Get system metrics history"""
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
    """Get IP blocking statistics"""
    return await ml_monitor.get_blocking_statistics()

@app.get("/api/blocking/ips")
async def get_blocked_ips_list():
    """Get list of blocked IPs"""
    return await ml_monitor.get_blocked_ips()

@app.post("/api/blocking/block")
async def block_ip(request: dict):
    """Block an IP address"""
    try:
        monitoring_server_url = os.getenv("MONITORING_SERVER_URL", "http://localhost:5000")
        response = requests.post(
            f"{monitoring_server_url}/block-ip",
            json=request,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/blocking/unblock")
async def unblock_ip(request: dict):
    """Unblock an IP address"""
    try:
        monitoring_server_url = os.getenv("MONITORING_SERVER_URL", "http://localhost:5000")
        response = requests.post(
            f"{monitoring_server_url}/unblock-ip",
            json=request,
            timeout=10
        )
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("DASHBOARD_PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
