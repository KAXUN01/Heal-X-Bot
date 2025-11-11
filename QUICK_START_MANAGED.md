# Quick Start: Self-Managing Services

## 🚀 Quick Commands

### Start All Services (Self-Managed)
```bash
./start-managed.sh
```

### Check Service Status
```bash
./check-services.sh
```

### Stop All Services
```bash
./stop-services.sh
```

## 📋 What's Different?

The new `start-managed.sh` script provides:

✅ **Auto-restart** - Services automatically restart if they crash  
✅ **Health monitoring** - Continuous health checks every 10 seconds  
✅ **Status tracking** - Real-time status in `.service_status.json`  
✅ **Smart restart limits** - Prevents restart loops (max 5 restarts per 5 min)  
✅ **Better logging** - Enhanced logging with service-specific logs  
✅ **Graceful shutdown** - Proper cleanup on exit  

## 🎯 Key Features

### Auto-Restart on Crash
If a service crashes, it will automatically restart (up to 5 times per 5 minutes).

### Health Checks
Each service is monitored via HTTP health endpoints:
- Model API: `http://localhost:8080/health`
- Network Analyzer: `http://localhost:8000/health`
- ML Dashboard: `http://localhost:3001/`
- Incident Bot: `http://localhost:8001/health`
- Monitoring Server: `http://localhost:5000/health`
- Healing Dashboard: `http://localhost:5001/`

### Status Tracking
Check service status anytime:
```bash
./check-services.sh
```

Or check the status file:
```bash
cat .service_status.json
```

### PID Management
PID files are stored in `.pids/` directory for each service.

### Logs
Service logs are in `logs/` directory:
- `logs/DDoS Model API.log`
- `logs/ML Dashboard.log`
- etc.

## 📊 Service Status

Services can be in one of these states:
- ✅ **running** - Service is running and healthy
- 🟡 **starting** - Service is starting up
- 🔴 **crashed** - Service crashed (will auto-restart)
- 🟠 **unhealthy** - Health check failed (will restart)
- ⚪ **stopped** - Service was stopped
- ❌ **failed** - Service failed to start
- 🛑 **max_restarts** - Exceeded restart limit

## 🔧 Configuration

Edit configuration in `start-managed.sh`:
```bash
MONITOR_INTERVAL=10      # Check every 10 seconds
RESTART_DELAY=5          # Wait 5 seconds before restart
MAX_RESTARTS=5           # Max restarts per 5 minutes
HEALTH_CHECK_TIMEOUT=3   # Health check timeout
```

## 🐛 Troubleshooting

### Service Keeps Crashing
1. Check logs: `tail -f logs/[Service Name].log`
2. Check status: `./check-services.sh`
3. Manual test: `python3 [path]/[script].py`

### Service Not Starting
1. Check Python: `python3 --version` (needs 3.8+)
2. Check dependencies: `pip install -r requirements.txt`
3. Check port: `lsof -i :[port]`

### Health Check Failing
1. Test endpoint: `curl http://localhost:[port]/health`
2. Check service logs
3. Increase timeout in config

## 📚 More Information

See `MANAGED_SERVICES_README.md` for detailed documentation.

## 🆚 Comparison

| Feature | start.sh | start-managed.sh |
|---------|----------|------------------|
| Auto-restart | ❌ | ✅ |
| Health checks | ❌ | ✅ |
| Status tracking | ❌ | ✅ |
| Restart limits | ❌ | ✅ |
| Monitoring | ❌ | ✅ |

---

**🛡️ Use `start-managed.sh` for production deployments!**

