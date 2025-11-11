# Self-Managing Service Manager

This document describes the improved self-managing startup script that automatically monitors, restarts, and maintains all Healing-Bot services.

## Features

### 🚀 **Auto-Restart on Crash**
- Services automatically restart if they crash or stop unexpectedly
- Configurable maximum restart attempts (default: 5 per 5 minutes)
- Exponential backoff to prevent restart loops

### 🏥 **Health Monitoring**
- Continuous health checks every 10 seconds (configurable)
- HTTP health endpoint monitoring
- Automatic restart on health check failures
- Process status tracking

### 📊 **Service Status Tracking**
- Real-time status for each service
- PID file management
- Status JSON file for external monitoring
- Service state tracking (running, crashed, unhealthy, stopped)

### 🛡️ **Graceful Shutdown**
- Proper cleanup on Ctrl+C
- Stops all services gracefully
- Cleans up PID files
- Stops Fluent Bit container

### 📝 **Enhanced Logging**
- Separate log files for each service
- Structured logging with colors
- Debug mode support
- Service-specific log rotation

## Usage

### Start All Services (Self-Managed)

```bash
./start-managed.sh
```

This will:
1. Check Python version and dependencies
2. Set up virtual environment
3. Install/update dependencies
4. Start all services
5. Begin monitoring loop
6. Auto-restart crashed services
7. Perform health checks

### Check Service Status

```bash
./check-services.sh
```

This shows:
- Service status (Running/Crashed/Stopped)
- Process IDs
- Port numbers
- Health check results
- Fluent Bit status

### Stop All Services

```bash
./stop-services.sh
```

This gracefully stops:
- All Python services
- Fluent Bit container
- Cleans up PID files

## Configuration

Edit the configuration variables in `start-managed.sh`:

```bash
MONITOR_INTERVAL=10      # Check service health every 10 seconds
RESTART_DELAY=5          # Wait 5 seconds before restarting
MAX_RESTARTS=5           # Maximum restart attempts per 5 minutes
HEALTH_CHECK_TIMEOUT=3   # Timeout for health checks in seconds
```

## Service Definitions

Services are defined in the `SERVICES` array:

```bash
SERVICES[service-name]="Display Name|path|script|port|env_vars|health_url"
```

Example:
```bash
SERVICES[model]="DDoS Model API|model|main.py|8080|MODEL_PORT=8080|http://localhost:8080/health"
```

## Service States

- **running**: Service is running and healthy
- **starting**: Service is starting up
- **crashed**: Service crashed and will be restarted
- **unhealthy**: Health check failed, will be restarted
- **stopped**: Service was manually stopped
- **failed**: Service failed to start
- **max_restarts**: Service exceeded maximum restart attempts

## Monitoring

### Status File

Service status is saved to `.service_status.json`:

```json
{
  "model": {"pid": 12345, "status": "running"},
  "dashboard": {"pid": 12346, "status": "running"},
  ...
}
```

### PID Files

PID files are stored in `.pids/` directory:
- `.pids/model.pid`
- `.pids/dashboard.pid`
- etc.

### Log Files

Log files are stored in `logs/` directory:
- `logs/DDoS Model API.log`
- `logs/ML Dashboard.log`
- etc.

## Health Checks

Each service has a health check URL that is monitored:
- **Model API**: `http://localhost:8080/health`
- **Network Analyzer**: `http://localhost:8000/health`
- **ML Dashboard**: `http://localhost:3001/`
- **Incident Bot**: `http://localhost:8001/health`
- **Monitoring Server**: `http://localhost:5000/health`
- **Healing Dashboard**: `http://localhost:5001/`

## Troubleshooting

### Service Keeps Crashing

1. Check the service log: `tail -f logs/[Service Name].log`
2. Check restart count: Look for "max_restarts" status
3. Manually test the service: `python3 [path]/[script].py`
4. Check dependencies: `pip list | grep [package]`

### Service Not Starting

1. Check Python version: `python3 --version` (requires 3.8+)
2. Check virtual environment: `source .venv/bin/activate`
3. Check dependencies: `pip install -r requirements.txt`
4. Check port availability: `lsof -i :[port]`

### Health Check Failing

1. Verify health endpoint is accessible: `curl http://localhost:[port]/health`
2. Check service logs for errors
3. Increase `HEALTH_CHECK_TIMEOUT` if service is slow to respond
4. Verify service is actually running: `ps aux | grep [service]`

### Docker/Fluent Bit Issues

1. Check Docker daemon: `sudo systemctl status docker`
2. Check Docker permissions: `docker ps` (may need sudo or docker group)
3. Check network: `docker network ls | grep healing-network`
4. Check Fluent Bit logs: `docker logs fluent-bit`

## Comparison with Original start.sh

| Feature | start.sh | start-managed.sh |
|---------|----------|------------------|
| Auto-restart | ❌ No | ✅ Yes |
| Health checks | ❌ No | ✅ Yes |
| Status tracking | ❌ No | ✅ Yes |
| Restart limits | ❌ No | ✅ Yes |
| PID management | ❌ Basic | ✅ Advanced |
| Service monitoring | ❌ No | ✅ Continuous |
| Graceful shutdown | ✅ Yes | ✅ Yes |
| Logging | ✅ Basic | ✅ Enhanced |

## Advanced Usage

### Debug Mode

Enable debug logging:
```bash
DEBUG=1 ./start-managed.sh
```

### Run in Background

```bash
nohup ./start-managed.sh > startup.log 2>&1 &
```

### Check Status Programmatically

```bash
cat .service_status.json | python3 -m json.tool
```

### Monitor Specific Service

```bash
tail -f logs/[Service Name].log
```

## Integration

### Systemd Service

Create `/etc/systemd/system/healing-bot.service`:

```ini
[Unit]
Description=Healing-Bot Self-Managing Service Manager
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Heal-X-Bot
ExecStart=/path/to/Heal-X-Bot/start-managed.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable healing-bot
sudo systemctl start healing-bot
sudo systemctl status healing-bot
```

## Best Practices

1. **Monitor Logs**: Regularly check service logs for errors
2. **Set Alerts**: Monitor `.service_status.json` for service failures
3. **Resource Limits**: Monitor system resources (CPU, memory, disk)
4. **Backup**: Regularly backup configuration and data
5. **Updates**: Keep dependencies up to date
6. **Testing**: Test service restarts in a development environment

## Support

For issues or questions:
1. Check service logs in `logs/` directory
2. Check status: `./check-services.sh`
3. Review this documentation
4. Check project README.md
5. Open an issue on GitHub

---

**🛡️ Stay Protected with Self-Managing AI-Powered Security!**

