# Services Page

## Description
The Services page provides comprehensive monitoring and management of all system services including Docker containers, systemd services, and Kubernetes pods. It enables service lifecycle management and health monitoring.

## Purpose
- Monitor all running services in real-time
- Control service lifecycle (start/stop/restart)
- View service health and dependencies
- Enable auto-restart functionality

## Features

### 1. Auto-Restart Toggle
- **Location**: Top right corner
- **Function**: Enable/disable automatic service restart on failure
- **Default**: Enabled
- **Scope**: Applies to all monitored services

### 2. Service List
Each service displays:

| Column | Description |
|--------|-------------|
| **Name** | Service/container name |
| **Type** | docker/systemd/kubernetes |
| **Status** | running/stopped/failed |
| **Health** | healthy/unhealthy |
| **Image** | Container image (Docker only) |
| **Actions** | Start/Stop/Restart buttons |

### 3. Service Actions
- **Start**: Launch stopped service
- **Stop**: Gracefully stop running service
- **Restart**: Stop and start service
- **Logs**: View recent service logs
- **Inspect**: View detailed service info

### 4. Status Indicators

| Status | Color | Icon | Description |
|--------|-------|------|-------------|
| Running | Green | ✅ | Service is healthy and running |
| Stopped | Gray | ⏹️ | Service is stopped |
| Failed | Red | ❌ | Service has crashed or errored |
| Starting | Yellow | ⏳ | Service is starting up |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/services` | GET | List all services |
| `/api/services/{name}` | GET | Get specific service |
| `/api/services/{name}/start` | POST | Start service |
| `/api/services/{name}/stop` | POST | Stop service |
| `/api/services/{name}/restart` | POST | Restart service |
| `/api/services/{name}/logs` | GET | Get service logs |

## Service Detection

### Docker Containers
```python
docker_client = docker.from_env()
containers = docker_client.containers.list(all=True)
```
- Excludes cloud-sim test containers
- Shows all containers (running and stopped)
- Provides container image information

### Systemd Services
```python
subprocess.run(["systemctl", "is-active", service_name])
```
- Monitors critical system services
- Categories: web, database, monitoring, security

### Kubernetes Pods
```python
kubectl get pods -o json
```
- Requires kubectl configured
- Shows namespace and phase

## Service Categories

### Critical Services Monitored
```python
services = {
    "web": ["nginx", "apache2", "caddy"],
    "database": ["mysql", "postgresql", "redis"],
    "monitoring": ["prometheus", "grafana", "fluent-bit"],
    "security": ["fail2ban", "ufw", "apparmor"]
}
```

## Technical Implementation

### Service Status Check
```python
def check_service_status(service_name, service_type=None):
    if service_type == 'docker':
        return check_docker_container_status(service_name)
    elif service_type == 'kubernetes':
        return check_kubernetes_service_status(service_name)
    else:
        return check_systemd_service_status(service_name)
```

### Auto-Restart Logic
```python
if auto_restart_enabled and service.status == 'failed':
    service.restart()
    send_discord_alert(f"Auto-restarted {service.name}")
```

### JavaScript Functions
```javascript
loadServices()           // Fetch all services
startService(name)       // Start a service
stopService(name)        // Stop a service
restartService(name)     // Restart a service
toggleAutoRestart()      // Toggle auto-restart mode
```

## User Actions
- Toggle auto-restart for all services
- Manually start/stop/restart individual services
- View service logs
- Inspect service details

## Related Pages
- [Overview](01_OVERVIEW.md) - Service count summary
- [Self-Healing](11_SELF_HEALING.md) - Automatic service recovery
- [Processes](05_PROCESSES.md) - Process-level view
