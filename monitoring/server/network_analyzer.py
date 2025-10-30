from fastapi import FastAPI, WebSocket
from typing import List, Dict
import asyncio
import json
import time
import numpy as np
from collections import defaultdict
import logging
from lightweight_cache import cache, set_cache, get_cache, delete_cache, cache_exists
from lightweight_storage import storage, index_document, search_documents, get_document, delete_document
from ip_blocker import ip_blocker
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize lightweight alternatives
logger.info("Using lightweight SQLite cache and JSON storage instead of Redis/Elasticsearch")

# Prometheus metrics
attack_detections_total = Counter('attack_detections_total', 'Total number of attack detections', ['attack_type'])
ip_blocks_total = Counter('ip_blocks_total', 'Total number of IPs blocked')
ip_unblocks_total = Counter('ip_unblocks_total', 'Total number of IPs unblocked')
network_analysis_duration_seconds = Histogram('network_analysis_duration_seconds', 'Time spent analyzing network traffic')
blocked_ips_gauge = Gauge('blocked_ips_gauge', 'Current number of blocked IPs')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.attack_patterns: Dict = defaultdict(int)
        self.ip_tracking: Dict = defaultdict(lambda: {'count': 0, 'first_seen': 0})

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    def analyze_attack_pattern(self, ip: str, request_data: dict) -> dict:
        current_time = time.time()
        
        # Check if IP is already blocked
        if ip_blocker.is_ip_blocked(ip):
            return {
                'ip': ip,
                'blocked': True,
                'reason': 'IP is currently blocked',
                'request_count': 0,
                'duration': 0,
                'pattern_detected': False,
                'attack_type': None,
                'confidence': 0.0
            }
        
        # Track IP behavior
        if ip not in self.ip_tracking:
            self.ip_tracking[ip] = {
                'count': 1,
                'first_seen': current_time,
                'requests': [],
                'bytes_sent': [],
                'intervals': []
            }
        else:
            track = self.ip_tracking[ip]
            track['count'] += 1
            track['requests'].append(current_time)
            track['bytes_sent'].append(request_data.get('bytes_sent', 0))
            
            if len(track['requests']) > 1:
                track['intervals'].append(
                    track['requests'][-1] - track['requests'][-2]
                )

        # Analyze patterns
        track = self.ip_tracking[ip]
        analysis = {
            'ip': ip,
            'request_count': track['count'],
            'duration': current_time - track['first_seen'],
            'pattern_detected': False,
            'attack_type': None,
            'confidence': 0.0,
            'threat_level': 0.0,
            'blocked': False
        }

        if len(track['requests']) > 10:  # Minimum requests for pattern analysis
            # Calculate metrics
            req_per_second = len(track['requests']) / (current_time - track['first_seen'])
            avg_bytes = np.mean(track['bytes_sent'])
            std_interval = np.std(track['intervals'])

            # Pattern detection
            if req_per_second > 100:  # High request rate
                analysis['pattern_detected'] = True
                analysis['attack_type'] = 'HTTP Flood'
                analysis['confidence'] = min(req_per_second / 200, 1.0)
                analysis['threat_level'] = min(req_per_second / 200, 1.0)
            
            elif std_interval < 0.1 and len(track['requests']) > 50:  # Very regular intervals
                analysis['pattern_detected'] = True
                analysis['attack_type'] = 'Bot Activity'
                analysis['confidence'] = 0.8
                analysis['threat_level'] = 0.8
            
            elif avg_bytes > 1000000:  # Large payload attacks
                analysis['pattern_detected'] = True
                analysis['attack_type'] = 'Volumetric Attack'
                analysis['confidence'] = min(avg_bytes / 2000000, 1.0)
                analysis['threat_level'] = min(avg_bytes / 2000000, 1.0)

        # Auto-block if threat level is high
        if analysis['pattern_detected'] and analysis['threat_level'] > 0:
            if ip_blocker.should_auto_block(ip, analysis['threat_level'], analysis['attack_type']):
                block_reason = f"High threat level ({analysis['threat_level']:.2f}) - {analysis['attack_type']}"
                if ip_blocker.block_ip(ip, block_reason, analysis['threat_level'], analysis['attack_type']):
                    analysis['blocked'] = True
                    analysis['block_reason'] = block_reason
                    logger.warning(f"Auto-blocked IP {ip} due to high threat level: {analysis['threat_level']:.2f}")

        return analysis

    async def store_attack_data(self, analysis: dict):
        """Store attack data using lightweight storage"""
        if analysis['pattern_detected']:
            try:
                index_document(
                    index_name='attack-patterns',
                    document={
                        'timestamp': time.time(),
                        'ip': analysis['ip'],
                        'attack_type': analysis['attack_type'],
                        'confidence': analysis['confidence'],
                        'request_count': analysis['request_count'],
                        'duration': analysis['duration']
                    }
                )
                logger.info(f"Stored attack pattern for IP {analysis['ip']}")
            except Exception as e:
                logger.error(f"Error storing attack data: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Analyze traffic patterns
            ip = request_data.get('ip', 'unknown')
            analysis = manager.analyze_attack_pattern(ip, request_data)
            
            # Store attack data if pattern detected
            if analysis['pattern_detected']:
                await manager.store_attack_data(analysis)
                
                # Store in lightweight cache for real-time alerts
                alert_key = f"attack:{ip}:{time.time()}"
                set_cache(alert_key, analysis, expire=3600)  # 1 hour expiry
            
            # Broadcast analysis
            await manager.broadcast(json.dumps(analysis))
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        manager.disconnect(websocket)

@app.get("/attack-patterns")
async def get_attack_patterns():
    """Get historical attack patterns"""
    try:
        # Get patterns from last 24 hours
        cutoff_time = time.time() - (24 * 60 * 60)  # 24 hours ago
        
        result = search_documents(
            index_name="attack-patterns",
            query={
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": cutoff_time
                        }
                    }
                }
            },
            size=1000
        )
        
        # Process results for aggregation
        attack_types = {}
        timeline = {}
        
        for hit in result.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            attack_type = source.get("attack_type", "Unknown")
            timestamp = source.get("timestamp", 0)
            
            # Count attack types
            attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
            
            # Group by hour for timeline
            hour_key = int(timestamp // 3600) * 3600
            timeline[hour_key] = timeline.get(hour_key, 0) + 1
        
        return {
            "hits": result.get("hits", {}),
            "aggregations": {
                "attack_types": [{"key": k, "doc_count": v} for k, v in attack_types.items()],
                "timeline": [{"key": k, "doc_count": v} for k, v in sorted(timeline.items())]
            }
        }
    except Exception as e:
        logger.error(f"Error getting attack patterns: {e}")
        return {"hits": {"total": {"value": 0}, "hits": []}, "aggregations": {}}

@app.get("/active-threats")
async def get_active_threats():
    """Get currently active threats"""
    try:
        threats = []
        # Get all cache keys that start with "attack:"
        all_keys = cache.get_all_keys()
        attack_keys = [key for key in all_keys if key.startswith("attack:")]
        
        for key in attack_keys:
            threat_data = get_cache(key)
            if threat_data:
                threats.append(threat_data)
        
        return {"threats": threats}
    except Exception as e:
        logger.error(f"Error getting active threats: {e}")
        return {"threats": []}

@app.get("/blocked-ips")
async def get_blocked_ips():
    """Get list of blocked IPs"""
    try:
        blocked_ips = ip_blocker.get_blocked_ips(active_only=True)
        return {"blocked_ips": blocked_ips}
    except Exception as e:
        logger.error(f"Error getting blocked IPs: {e}")
        return {"blocked_ips": []}

@app.get("/blocked-ips/stats")
async def get_blocking_statistics():
    """Get IP blocking statistics"""
    try:
        stats = ip_blocker.get_blocking_statistics()
        return {"statistics": stats}
    except Exception as e:
        logger.error(f"Error getting blocking statistics: {e}")
        return {"statistics": {}}

@app.post("/block-ip")
async def block_ip_endpoint(request: dict):
    """Manually block an IP address"""
    try:
        ip = request.get('ip')
        reason = request.get('reason', 'Manual block')
        threat_level = request.get('threat_level', 0.0)
        attack_type = request.get('attack_type', 'Manual')
        
        if not ip:
            return {"error": "IP address is required"}
        
        success = ip_blocker.block_ip(ip, reason, threat_level, attack_type, auto_blocked=False)
        
        if success:
            # Record metrics
            ip_blocks_total.inc()
            blocked_ips_gauge.inc()
            return {"status": "success", "message": f"IP {ip} blocked successfully"}
        else:
            return {"status": "error", "message": f"Failed to block IP {ip}"}
            
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/unblock-ip")
async def unblock_ip_endpoint(request: dict):
    """Unblock an IP address"""
    try:
        ip = request.get('ip')
        
        if not ip:
            return {"error": "IP address is required"}
        
        success = ip_blocker.unblock_ip(ip)
        
        if success:
            # Record metrics
            ip_unblocks_total.inc()
            blocked_ips_gauge.dec()
            return {"status": "success", "message": f"IP {ip} unblocked successfully"}
        else:
            return {"status": "error", "message": f"Failed to unblock IP {ip} or IP not found"}
            
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/is-blocked/{ip}")
async def check_ip_blocked(ip: str):
    """Check if an IP is blocked"""
    try:
        is_blocked = ip_blocker.is_ip_blocked(ip)
        return {"ip": ip, "blocked": is_blocked}
    except Exception as e:
        logger.error(f"Error checking IP block status: {e}")
        return {"ip": ip, "blocked": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)