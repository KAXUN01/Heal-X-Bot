from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
import time
import threading
import psutil
import platform
import requests
from datetime import datetime
from prometheus_client import Counter, generate_latest, Gauge, CONTENT_TYPE_LATEST
from flask_bootstrap import Bootstrap
import numpy as np
from collections import deque
import json
import os
from pathlib import Path
from dotenv import load_dotenv
try:
    from .log_monitor import initialize_log_monitoring, log_monitor
except ImportError:
    from log_monitor import initialize_log_monitoring, log_monitor
try:
    from .centralized_logger import initialize_centralized_logging, centralized_logger
except ImportError:
    from centralized_logger import initialize_centralized_logging, centralized_logger
try:
    from .service_discovery import ServiceDiscovery
except ImportError:
    from service_discovery import ServiceDiscovery
try:
    from .gemini_log_analyzer import initialize_gemini_analyzer, gemini_analyzer
except ImportError:
    from gemini_log_analyzer import initialize_gemini_analyzer, gemini_analyzer
try:
    from .system_log_collector import initialize_system_log_collector, get_system_log_collector
except ImportError:
    from system_log_collector import initialize_system_log_collector, get_system_log_collector
try:
    from .critical_services_monitor import initialize_critical_services_monitor, get_critical_services_monitor
except ImportError:
    from critical_services_monitor import initialize_critical_services_monitor, get_critical_services_monitor
try:
    from .healing import initialize_auto_healer, get_auto_healer
except ImportError:
    # Fallback to old import path for backward compatibility
    try:
        from auto_healer import initialize_auto_healer, get_auto_healer
    except ImportError:
        # If running as module, try absolute import
        try:
            from monitoring.server.healing import initialize_auto_healer, get_auto_healer
        except ImportError:
            # Last resort: import directly from healing directory
            import sys
            from pathlib import Path
            healing_path = Path(__file__).parent / 'healing'
            if healing_path.exists():
                sys.path.insert(0, str(Path(__file__).parent))
                from healing import initialize_auto_healer, get_auto_healer

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Verify critical environment variables
if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
    print("⚠️  WARNING: GEMINI_API_KEY not found in .env file")
    print("   AI log analysis will not work without this key")
    print("   Please add GEMINI_API_KEY to your .env file")

app = Flask(__name__)
# Set Flask configuration to avoid KeyError (must be set before Bootstrap)
# Flask 3.1.0 requires this config to be set explicitly
if 'PROVIDE_AUTOMATIC_OPTIONS' not in app.config:
    app.config['PROVIDE_AUTOMATIC_OPTIONS'] = True
bootstrap = Bootstrap(app)

# Enable CORS for all routes to allow dashboard to access the API
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize monitoring services on startup
log_monitoring_service = None
centralized_logging_service = None
centralized_logger = None  # Alias for endpoints
service_discovery = None
gemini_log_analyzer_service = None
gemini_analyzer = None  # Alias for endpoints
log_monitor = None  # Alias for endpoints
system_log_collector = None  # System-wide log collector
critical_services_monitor = None  # Critical services monitor
auto_healer = None  # AI-powered auto-healing system

# Prometheus metrics
REQUEST_COUNT = Counter("request_count", "Total number of requests", ['endpoint'])
CPU_LOAD = Gauge("cpu_load_simulation", "Simulated CPU Load")
MEMORY_USAGE = Gauge("memory_usage_percent", "System memory usage")
SYSTEM_CPU_USAGE = Gauge("system_cpu_percent", "System CPU usage")
NETWORK_IN = Gauge("network_in_bytes", "Network incoming bytes")
NETWORK_OUT = Gauge("network_out_bytes", "Network outgoing bytes")
CONNECTIONS = Gauge("active_connections", "Number of active connections")
DDOS_PROBABILITY = Gauge("ddos_probability", "DDoS attack probability")

# Store historical data for graphs
MAX_HISTORY = 100
metrics_history = {
    'timestamps': deque(maxlen=MAX_HISTORY),
    'cpu': deque(maxlen=MAX_HISTORY),
    'memory': deque(maxlen=MAX_HISTORY),
    'network_in': deque(maxlen=MAX_HISTORY),
    'network_out': deque(maxlen=MAX_HISTORY),
    'connections': deque(maxlen=MAX_HISTORY),
    'ddos_prob': deque(maxlen=MAX_HISTORY)
}

def get_network_stats():
    """Get network statistics"""
    net_io = psutil.net_io_counters()
    connections = len(psutil.net_connections())
    return net_io.bytes_recv, net_io.bytes_sent, connections

def get_system_metrics():
    """Gather system metrics"""
    try:
        # Basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network metrics
        net_in, net_out, conn_count = get_network_stats()
        
        # Update Prometheus metrics
        SYSTEM_CPU_USAGE.set(cpu_percent)
        MEMORY_USAGE.set(memory_percent)
        CPU_LOAD.set(cpu_percent)
        NETWORK_IN.set(net_in)
        NETWORK_OUT.set(net_out)
        CONNECTIONS.set(conn_count)
        
        # Update historical data
        current_time = datetime.now().strftime('%H:%M:%S')
        metrics_history['timestamps'].append(current_time)
        metrics_history['cpu'].append(cpu_percent)
        metrics_history['memory'].append(memory_percent)
        metrics_history['network_in'].append(net_in)
        metrics_history['network_out'].append(net_out)
        metrics_history['connections'].append(conn_count)
        CPU_LOAD.set(cpu_percent)
        
        return {
            'cpu': cpu_percent,
            'memory': memory_percent,
            'disk': disk_percent,
            'memory_available': memory.available / (1024 * 1024 * 1024),  # GB
            'disk_free': disk.free / (1024 * 1024 * 1024)  # GB
        }
    except Exception as e:
        app.logger.error(f"Error collecting system metrics: {str(e)}")
        return {
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'memory_available': 0,
            'disk_free': 0,
            'error': str(e)
        }

@app.route('/')
def index():
    """API Server - No web UI, use dashboard at port 5001"""
    REQUEST_COUNT.labels(endpoint="/").inc()
    return jsonify({
        'status': 'success',
        'message': 'Healing-bot Monitoring API Server',
        'version': '2.0',
        'info': 'This is an API-only server. For the web UI, visit http://localhost:5001',
        'endpoints': {
            'health': '/health',
            'metrics': '/metrics (Prometheus)',
            'logs_api': '/api/logs/*',
            'system_logs': '/api/system-logs/*',
            'critical_services': '/api/critical-services/*',
            'ai_analysis': '/api/gemini/*',
            'service_discovery': '/api/discovery/*'
        },
        'documentation': 'See docs/ folder for complete API documentation'
    })

@app.route("/metrics")
def metrics():
    """Return Prometheus metrics"""
    get_system_metrics()  # Update metrics before returning
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/cpu")
def cpu_intensive():
    """Simulate CPU intensive task"""
    REQUEST_COUNT.labels(endpoint="/cpu").inc()

    def burn_cpu():
        start = time.time()
        while time.time() - start < 60:
            _ = [x ** 2 for x in range(10000)]
        CPU_LOAD.set(0.0)

    thread = threading.Thread(target=burn_cpu)
    thread.start()
    return "Started CPU load for 60 seconds!"

# ========== Log Monitoring Endpoints ==========

@app.route("/api/logs/recent")
def get_recent_log_issues():
    """Get recent log issues"""
    try:
        limit = int(request.args.get('limit', 50))
        issues = log_monitor.get_recent_issues(limit=limit)
        return jsonify({
            'status': 'success',
            'issues': issues,
            'count': len(issues)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/logs/statistics")
def get_log_statistics():
    """Get log monitoring statistics"""
    try:
        stats = log_monitor.get_issue_statistics()
        health_score = log_monitor.get_system_health_score()
        
        return jsonify({
            'status': 'success',
            'statistics': stats,
            'health_score': health_score
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/logs/critical")
def get_critical_log_issues():
    """Get critical unresolved issues"""
    try:
        if not log_monitor:
            return jsonify({
                'status': 'success',
                'critical_issues': [],
                'count': 0
            })
        critical_issues = log_monitor.get_critical_issues()
        return jsonify({
            'status': 'success',
            'critical_issues': critical_issues,
            'count': len(critical_issues)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/logs/anomalies")
def get_log_anomalies():
    """Get detected anomalies in logs"""
    try:
        if not log_monitor:
            return jsonify({
                'status': 'success',
                'anomalies': [],
                'count': 0
            })
        
        # Get anomalies from log monitor
        anomalies = []
        if hasattr(log_monitor, 'get_anomalies'):
            anomalies = log_monitor.get_anomalies()
        elif hasattr(log_monitor, 'detect_anomalies'):
            anomalies = log_monitor.detect_anomalies()
        
        # Also check centralized logger for anomalies
        if centralized_logger and hasattr(centralized_logger, 'get_anomalies'):
            central_anomalies = centralized_logger.get_anomalies()
            if central_anomalies:
                anomalies.extend(central_anomalies)
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies,
            'count': len(anomalies)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'anomalies': [],
            'count': 0
        }), 200

@app.route("/api/system-logs/recent")
def get_system_logs():
    """Get recent system-wide logs (Docker, syslog, systemd, etc.)"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return jsonify({
                'status': 'error',
                'message': 'System log collector not initialized',
                'logs': []
            }), 503
        
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', None)
        source = request.args.get('source', None)
        
        # Get logs
        logs = collector.get_recent_logs(limit=limit, level=level, source=source)
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'logs': []
        }), 500

@app.route("/api/system-logs/statistics")
def get_system_log_statistics():
    """Get statistics about system-wide logs"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return jsonify({
                'status': 'error',
                'message': 'System log collector not initialized'
            }), 503
        
        stats = collector.get_log_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/system-logs/sources")
def get_system_log_sources():
    """Get available system log sources"""
    try:
        collector = get_system_log_collector()
        
        if not collector:
            return jsonify({
                'status': 'error',
                'message': 'System log collector not initialized'
            }), 503
        
        sources = []
        for source_name, config in collector.log_sources.items():
            sources.append({
                'name': source_name,
                'enabled': config['enabled'],
                'description': f'{source_name.capitalize()} logs'
            })
        
        return jsonify({
            'status': 'success',
            'sources': sources
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Critical Services Monitor Endpoints

@app.route("/api/critical-services/list")
def get_critical_services_list():
    """Get list of all critical services by category"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return jsonify({
                'status': 'error',
                'message': 'Critical services monitor not initialized'
            }), 503
        
        service_list = monitor.get_service_list()
        
        return jsonify({
            'status': 'success',
            'services': service_list
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/critical-services/logs")
def get_critical_services_logs():
    """Get logs from critical services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return jsonify({
                'status': 'error',
                'message': 'Critical services monitor not initialized'
            }), 503
        
        # Get query parameters
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level', None)
        category = request.args.get('category', None)
        service = request.args.get('service', None)
        
        # Get logs based on filters
        if category:
            logs = monitor.get_logs_by_category(category, limit=limit)
        elif service:
            logs = monitor.get_logs_by_service(service, limit=limit)
        else:
            logs = monitor.get_recent_logs(limit=limit, level=level)
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'logs': []
        }), 500

@app.route("/api/critical-services/issues")
def get_critical_service_issues():
    """Get critical issues from monitored services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return jsonify({
                'status': 'error',
                'message': 'Critical services monitor not initialized'
            }), 503
        
        issues = monitor.get_critical_issues()
        
        return jsonify({
            'status': 'success',
            'issues': issues,
            'count': len(issues)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'issues': []
        }), 500

@app.route("/api/critical-services/statistics")
def get_critical_services_statistics():
    """Get statistics about critical services"""
    try:
        monitor = get_critical_services_monitor()
        
        if not monitor:
            return jsonify({
                'status': 'error',
                'message': 'Critical services monitor not initialized'
            }), 503
        
        stats = monitor.get_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/logs/health")
def get_system_health():
    """Get overall system health score"""
    try:
        health_score = log_monitor.get_system_health_score()
        recent_issues = len(log_monitor.recent_issues)
        
        # Determine health status
        if health_score >= 90:
            status = 'healthy'
        elif health_score >= 70:
            status = 'warning'
        elif health_score >= 50:
            status = 'degraded'
        else:
            status = 'critical'
        
        return jsonify({
            'status': 'success',
            'health_score': health_score,
            'health_status': status,
            'recent_issues_count': recent_issues
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/logs/resolve/<timestamp>", methods=['POST'])
def resolve_issue(timestamp):
    """Mark an issue as resolved"""
    try:
        log_monitor.mark_issue_resolved(timestamp)
        return jsonify({
            'status': 'success',
            'message': 'Issue marked as resolved'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'monitoring-server'
    })

# ========== Centralized Logging Endpoints ==========

@app.route("/api/central-logs/statistics")
def get_central_log_statistics():
    """Get centralized logging statistics"""
    try:
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logging not initialized'
            }), 503
        
        stats = centralized_logger.get_statistics()
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/central-logs/recent")
def get_central_recent_logs():
    """Get recent centralized logs"""
    try:
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logging not initialized'
            }), 503
        
        limit = int(request.args.get('limit', 100))
        logs = centralized_logger.get_recent_logs(limit=limit)
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/central-logs/search")
def search_central_logs():
    """Search centralized logs"""
    try:
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logging not initialized'
            }), 503
        
        query = request.args.get('query', '')
        service = request.args.get('service', None)
        limit = int(request.args.get('limit', 100))
        
        logs = centralized_logger.search_logs(query=query, service=service, limit=limit)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'service': service,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/central-logs/by-service/<service>")
def get_logs_by_service(service):
    """Get logs for a specific service"""
    try:
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logging not initialized'
            }), 503
        
        limit = int(request.args.get('limit', 100))
        logs = centralized_logger.get_logs_by_service(service=service, limit=limit)
        
        return jsonify({
            'status': 'success',
            'service': service,
            'logs': logs,
            'count': len(logs)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/central-logs/services")
def get_monitored_services():
    """Get list of all monitored services"""
    try:
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logging not initialized'
            }), 503
        
        services = centralized_logger.get_service_list()
        
        return jsonify({
            'status': 'success',
            'services': services,
            'count': len(services)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ========== Service Discovery Endpoints ==========

@app.route("/api/discovery/services")
def discover_services():
    """Discover all installed services and programs"""
    try:
        discovery = ServiceDiscovery()
        results = discovery.discover_all_services()
        summary = discovery.get_summary()
        
        return jsonify({
            'status': 'success',
            'summary': summary,
            'services': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/discovery/log-locations")
def get_log_locations():
    """Get all discovered log file locations"""
    try:
        discovery = ServiceDiscovery()
        discovery.discover_all_services()
        log_locations = discovery.get_log_locations()
        
        return jsonify({
            'status': 'success',
            'log_locations': log_locations,
            'total_services': len(log_locations),
            'total_log_files': sum(len(logs) for logs in log_locations.values())
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/discovery/summary")
def get_discovery_summary():
    """Get service discovery summary"""
    try:
        if not service_discovery:
            discovery = ServiceDiscovery()
            discovery.discover_all_services()
            summary = discovery.get_summary()
        else:
            summary = service_discovery.get_summary()
        
        return jsonify({
            'status': 'success',
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ========== Gemini AI Log Analysis Endpoints ==========

@app.route("/api/gemini/analyze-log", methods=['POST'])
def analyze_single_log():
    """Analyze a single log entry using Gemini AI"""
    try:
        if not gemini_analyzer:
            return jsonify({
                'status': 'error',
                'message': 'Gemini analyzer not initialized. Check GEMINI_API_KEY'
            }), 503
        
        log_entry = request.json
        
        if not log_entry:
            return jsonify({
                'status': 'error',
                'message': 'No log entry provided'
            }), 400
        
        # Analyze the log
        analysis = gemini_analyzer.analyze_error_log(log_entry)
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/gemini/analyze-pattern", methods=['POST'])
def analyze_log_pattern():
    """Analyze multiple logs for patterns using Gemini AI"""
    try:
        if not gemini_analyzer:
            return jsonify({
                'status': 'error',
                'message': 'Gemini analyzer not initialized'
            }), 503
        
        data = request.json
        log_entries = data.get('logs', [])
        limit = data.get('limit', 10)
        
        if not log_entries:
            return jsonify({
                'status': 'error',
                'message': 'No log entries provided'
            }), 400
        
        # Analyze patterns
        analysis = gemini_analyzer.analyze_multiple_logs(log_entries, limit=limit)
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/gemini/analyze-service/<service_name>")
def analyze_service_health(service_name):
    """Analyze overall health of a service using Gemini AI"""
    try:
        if not gemini_analyzer:
            return jsonify({
                'status': 'error',
                'message': 'Gemini analyzer not initialized'
            }), 503
        
        if not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Centralized logger not initialized'
            }), 503
        
        # Get logs for the service
        limit = int(request.args.get('limit', 50))
        logs = centralized_logger.get_logs_by_service(service_name, limit=limit)
        
        if not logs:
            return jsonify({
                'status': 'error',
                'message': f'No logs found for service: {service_name}'
            }), 404
        
        # Analyze service health
        analysis = gemini_analyzer.analyze_service_health(service_name, logs)
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/gemini/quick-analyze")
def quick_analyze_recent_errors():
    """Quick analysis of recent errors from centralized logs"""
    try:
        if not gemini_analyzer or not centralized_logger:
            return jsonify({
                'status': 'error',
                'message': 'Services not initialized'
            }), 503
        
        # Get recent logs
        recent_logs = centralized_logger.get_recent_logs(limit=100)
        
        # Filter for errors/warnings
        error_logs = [
            log for log in recent_logs
            if any(keyword in log.get('message', '').lower() 
                  for keyword in ['error', 'fail', 'exception', 'critical', 'warning'])
        ]
        
        if not error_logs:
            return jsonify({
                'status': 'success',
                'message': 'No recent errors found',
                'error_count': 0
            })
        
        # Analyze top errors
        analysis = gemini_analyzer.analyze_multiple_logs(error_logs[:10])
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def initialize_services():
    """Initialize all monitoring services"""
    global log_monitoring_service, centralized_logging_service, centralized_logger
    global service_discovery, gemini_log_analyzer_service, gemini_analyzer, log_monitor
    global system_log_collector, critical_services_monitor, auto_healer
    
    try:
        # DISABLED: Application log monitoring (not needed - only monitoring system services)
        # log_monitoring_service = initialize_log_monitoring()
        # log_monitor = log_monitoring_service
        print("⚠️  Application log monitoring DISABLED (monitoring system services only)")
        
        # DISABLED: Centralized logging (was creating 348 MB files!)
        # centralized_logging_service = initialize_centralized_logging()
        # centralized_logger = centralized_logging_service
        print("⚠️  Centralized logging DISABLED (monitoring system services only)")
        
        # DISABLED: Service discovery (not needed for system monitoring)
        # service_discovery = ServiceDiscovery()
        # service_discovery.discover_all_services()
        print("⚠️  Service discovery DISABLED (monitoring system services only)")
        
        # Initialize Gemini AI log analyzer (for system log analysis)
        gemini_log_analyzer_service = initialize_gemini_analyzer()
        gemini_analyzer = gemini_log_analyzer_service  # Set alias for endpoints
        print("✅ Gemini AI log analyzer initialized")
        
        # Initialize system-wide log collector (monitors Docker, systemd, etc.)
        system_log_collector = initialize_system_log_collector()
        print("✅ System-wide log collector initialized")
        
        # Initialize critical services monitor (focused monitoring of essential services)
        critical_services_monitor = initialize_critical_services_monitor()
        print("✅ Critical services monitor initialized")
        print("   📊 Monitoring critical services: Docker, systemd-journald, dbus, cron, etc.")
        
        # Initialize cloud simulation components
        try:
            from container_healer import initialize_container_healer
            from root_cause_analyzer import initialize_root_cause_analyzer
            from fault_detector import initialize_fault_detector
            
            # Discord notifier function (simple implementation for app.py)
            def discord_notifier(message, severity="info", embed_data=None):
                # Simple Discord notification - can be enhanced
                try:
                    import requests
                    discord_webhook = os.getenv("DISCORD_WEBHOOK") or os.getenv("DISCORD_WEBHOOK_URL", "")
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
            
            # Initialize root cause analyzer
            root_cause_analyzer = initialize_root_cause_analyzer(
                gemini_analyzer=gemini_analyzer
            )
            
            # Initialize fault detector
            fault_detector = initialize_fault_detector(
                discord_notifier=discord_notifier
            )
            fault_detector.start_monitoring(interval=30)
            print("✅ Cloud fault detector initialized and started")
            
            # Initialize AI-powered auto-healer with cloud capabilities
            auto_healer = initialize_auto_healer(
                gemini_analyzer=gemini_analyzer,
                system_log_collector=system_log_collector,
                critical_services_monitor=critical_services_monitor,
                container_healer=container_healer,
                root_cause_analyzer=root_cause_analyzer,
                discord_notifier=discord_notifier
            )
            print("✅ AI-powered auto-healer initialized with cloud healing")
            print("   🤖 Auto-healing enabled: System will automatically fix detected errors")
            
            # Start auto-healing monitoring (check every 60 seconds)
            auto_healer.start_monitoring(interval_seconds=60)
            print("   ⚡ Auto-healing monitoring started (60s interval)")
        except Exception as e:
            print(f"⚠️  Cloud simulation components not available: {e}")
            # Fallback to basic auto-healer
            auto_healer = initialize_auto_healer(
                gemini_analyzer=gemini_analyzer,
                system_log_collector=system_log_collector,
                critical_services_monitor=critical_services_monitor
            )
            print("✅ Basic AI-powered auto-healer initialized")
            auto_healer.start_monitoring(interval_seconds=60)
        
        print(f"\n📊 Active Services:")
        print(f"   - gemini_analyzer: {gemini_analyzer is not None} (AI analysis)")
        print(f"   - system_log_collector: {system_log_collector is not None} (General system monitoring)")
        print(f"   - critical_services_monitor: {critical_services_monitor is not None} (Critical services)")
        print(f"   - auto_healer: {auto_healer is not None} (AI-powered self-healing)")
        print(f"\n💡 Monitoring CRITICAL SYSTEM SERVICES for failures/crashes")
        print(f"💡 Application logs DISABLED to save disk space")
        print(f"🤖 AI AUTO-HEALING ENABLED - System will self-repair automatically!")
        
        return True
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route("/api/test/inject-error", methods=['POST'])
def inject_test_error():
    """
    Inject a test error log for testing/demonstration purposes
    Request body: { 
        "service": "systemd-test",
        "message": "Test error message",
        "level": "ERROR",  # Optional, defaults to ERROR
        "source": "test"   # Optional, defaults to test
    }
    """
    global system_log_collector
    
    if not system_log_collector:
        return jsonify({
            'status': 'error',
            'message': 'System log collector not initialized'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request: JSON body required'
            }), 400
        
        service = data.get('service', 'test-service')
        message = data.get('message', 'Test error for anomaly detection')
        level = data.get('level', 'ERROR')
        source = data.get('source', 'test')
        
        # Inject the test log
        test_log = system_log_collector.inject_test_log(
            service=service,
            message=message,
            level=level,
            source=source
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Test error injected successfully',
            'log': test_log
        })
        
    except Exception as e:
        logger.error(f"Error injecting test error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Auto-Healing API Endpoints

@app.route("/api/auto-healer/status")
def get_auto_healer_status():
    """Get auto-healer status and configuration"""
    global auto_healer
    
    if not auto_healer:
        return jsonify({
            'status': 'error',
            'message': 'Auto-healer not initialized'
        }), 503
    
    try:
        return jsonify({
            'status': 'success',
            'auto_healer': {
                'enabled': auto_healer.enabled,
                'auto_execute': auto_healer.auto_execute,
                'monitoring': auto_healer.running,
                'max_attempts': auto_healer.max_healing_attempts,
                'monitoring_interval': getattr(auto_healer, 'monitoring_interval', 60)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/auto-healer/history")
def get_healing_history():
    """Get healing history"""
    global auto_healer
    
    if not auto_healer:
        return jsonify({
            'status': 'error',
            'message': 'Auto-healer not initialized'
        }), 503
    
    try:
        limit = int(request.args.get('limit', 50))
        history = auto_healer.get_healing_history(limit=limit)
        
        return jsonify({
            'status': 'success',
            'count': len(history),
            'history': history
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/auto-healer/statistics")
def get_healing_statistics():
    """Get healing statistics"""
    global auto_healer
    
    if not auto_healer:
        return jsonify({
            'status': 'error',
            'message': 'Auto-healer not initialized'
        }), 503
    
    try:
        stats = auto_healer.get_healing_statistics()
        
        return jsonify({
            'status': 'success',
            'statistics': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/auto-healer/heal", methods=['POST'])
def manual_heal_error():
    """Manually trigger healing for a specific error"""
    global auto_healer
    
    if not auto_healer:
        return jsonify({
            'status': 'error',
            'message': 'Auto-healer not initialized'
        }), 503
    
    try:
        error = request.get_json()
        
        if not error:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request: error log required'
            }), 400
        
        # Trigger healing
        result = auto_healer.heal_error(error)
        
        return jsonify({
            'status': 'success',
            'healing_result': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route("/api/auto-healer/config", methods=['PUT', 'POST'])
def update_auto_healer_config():
    """Update auto-healer configuration"""
    global auto_healer
    
    if not auto_healer:
        return jsonify({
            'status': 'error',
            'message': 'Auto-healer not initialized'
        }), 503
    
    try:
        data = request.get_json() or {}
        
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
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration updated successfully',
            'auto_healer': updated_config
        })
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    # Initialize all services before starting the app
    initialize_services()
    
    app.run(host="0.0.0.0", port=5000, debug=True)