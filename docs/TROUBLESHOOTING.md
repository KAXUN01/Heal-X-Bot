# Troubleshooting Guide

Common issues and solutions for Heal-X-Bot.

## Table of Contents

- [Installation & Startup](#installation--startup)
- [AI Analysis Issues](#ai-analysis-issues)
- [Port Conflicts](#port-conflicts)
- [Service Failures](#service-failures)
- [Docker Issues](#docker-issues)
- [Permission Errors](#permission-errors)

---

## Installation & Startup

### Python Version Error

**Error**: `Python 3.8 or higher required`

**Solution**:
```bash
# Check Python version
python3 --version

# Install Python 3.8+ if needed (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### pip install fails

**Error**: `error: externally-managed-environment`

**Solution**:
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
```bash
# Reinstall requirements
pip install -r requirements.txt

# For specific module
pip install module_name
```

---

## AI Analysis Issues

### "AI analyzer not initialized"

**Cause**: No API keys configured

**Solution**:
```bash
# Add Gemini key (recommended)
echo "GEMINI_API_KEY=your_key_here" >> .env

# Or add Groq key (alternative)
echo "GROQ_API_KEY=your_key_here" >> .env

# Restart server
pkill -f healing_dashboard_api
python3 monitoring/server/healing_dashboard_api.py
```

**Get API Keys**:
- Gemini: https://makersuite.google.com/app/apikey
- Groq: https://console.groq.com/

### "Model not available"

**Cause**: Invalid or expired API key

**Solution**:
```bash
# Test Gemini key
python3 test_gemini_key.py

# Test both providers
python3 test_ai_switching.py

# Check which provider is active
curl http://localhost:5001/api/gemini/status | jq
```

### Which AI provider is being used?

**Check startup logs**:
```
✅ Gemini AI analyzer initialized (model: gemini-2.5-flash-lite-preview-09-2025)
```
or
```
✅ Groq AI analyzer initialized (fallback from Gemini)
```

**Via API**:
```bash
curl http://localhost:5001/api/gemini/status
```

---

## Port Conflicts

### Port already in use

**Error**: `Address already in use: Port 5001`

**Solution**:
```bash
# Find process using port
sudo lsof -i :5001

# Kill process
kill -9 <PID>

# Or use different port
PORT=5002 python3 monitoring/server/healing_dashboard_api.py
```

### Common port conflicts

| Port | Service | Alternative |
|------|---------|-------------|
| 5001 | Healing Dashboard | 5002 |
| 5000 | Monitoring Server | 5050 |
| 8080 | ML Model | 8081 |
| 8000 | Network Analyzer | 8001 |

---

## Service Failures

### Service won't start

**1. Check logs**:
```bash
# View recent errors
tail -f logs/*.log

# Check specific service
python3 -m healx logs healing-dashboard
```

**2. Verify dependencies**:
```bash
# Test imports
python3 -c "import tensorflow; import fastapi; import groq"
```

**3. Check environment**:
```bash
# Verify .env file exists
cat .env | grep -E "API_KEY|WEBHOOK"
```

### Auto-healing not working

**Cause**: Auto-healer disabled or not initialized

**Solution**:
```bash
# Check auto-healer status
curl http://localhost:5001/api/auto-healer/status

# Enable auto-healing
curl -X POST http://localhost:5001/api/auto-healer/config \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "auto_execute": true}'
```

### Logs not showing

**Cause**: Log collector not initialized or insufficient permissions

**Solution**:
```bash
# Run with sudo for system logs
sudo python3 monitoring/server/healing_dashboard_api.py

# Or add user to journalctl group
sudo usermod -aG systemd-journal $USER

# Restart
```

---

## Docker Issues

### Docker not running

**Error**: `Cannot connect to Docker daemon`

**Solution**:
```bash
# Start Docker service
sudo systemctl start docker

# Enable on boot
sudo systemctl enable docker

# Check status
sudo systemctl status docker
```

### Container won't start

**Cause**: Port conflicts or image issues

**Solution**:
```bash
# Check container logs
docker logs <container_name>

# Restart container
docker restart <container_name>

# Rebuild if needed
docker-compose down
docker-compose up --build -d
```

### Permission denied

**Error**: `permission denied while trying to connect to Docker`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or:
newgrp docker

# Verify
docker ps
```

---

## Permission Errors

### Cannot read logs

**Error**: `Permission denied: '/var/log/syslog'`

**Solution**:
```bash
# Run with sudo
sudo python3 monitoring/server/app.py

# Or add read permissions (less secure)
sudo chmod 644 /var/log/syslog
```

### Cannot create database

**Error**: `Permission denied: 'monitoring/server/data/blocked_ips.db'`

**Solution**:
```bash
# Create data directory
mkdir -p monitoring/server/data

# Set permissions
chmod 755 monitoring/server/data
```

---

## Database Issues

### SQLite database locked

**Error**: `database is locked`

**Solution**:
```bash
# Kill other processes accessing DB
pkill -f healing_dashboard_api
pkill -f app.py

# Delete lock if present
rm monitoring/server/data/*.db-wal
rm monitoring/server/data/*.db-shm

# Restart
```

### Database corrupted

**Solution**:
```bash
# Backup current database
cp monitoring/server/data/blocked_ips.db monitoring/server/data/blocked_ips.db.backup

# Delete and restart (will recreate)
rm monitoring/server/data/blocked_ips.db
```

---

## Network Issues

### Cannot reach API endpoints

**Cause**: Firewall blocking or service not listening

**Solution**:
```bash
# Check if service is listening
netstat -tlnp | grep :5001

# Check firewall
sudo ufw status

# Allow port
sudo ufw allow 5001
```

### Discord/Slack webhooks not working

**Cause**: Invalid webhook URL or network restrictions

**Solution**:
```bash
# Test webhook manually
curl -X POST "YOUR_DISCORD_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'

# Check .env configuration
cat .env | grep WEBHOOK

# Verify URL format (should start with https://)
```

---

## Performance Issues

### High CPU usage

**Cause**: Too many services or inefficient code

**Solution**:
```bash
# Check processes
top -o %CPU

# Reduce monitoring interval
# Edit healing_dashboard_api.py
monitoring_interval = 120  # Increase from 60

# Disable unnecessary features
```

### High memory usage

**Cause**: Log caching or memory leaks

**Solution**:
```bash
# Clear log cache
curl -X POST http://localhost:5001/api/cache/clear

# Restart services
./start.sh restart

# Monitor memory
watch -n 2 free -h
```

---

## ML Model Issues

### Model not found

**Error**: `FileNotFoundError: ddos_model.keras`

**Solution**:
```bash
# Train new model
cd model
python3 train_model.py

# Or download pre-trained model
# (if available from repository)
```

### Low prediction accuracy

**Cause**: Model needs retraining with more data

**Solution**:
```bash
# Collect new training data
python3 model/collect_training_data.py

# Retrain model
python3 model/train_model.py

# Verify accuracy
python3 model/verify_model.py
```

---

## Cloud Simulation Issues

### Fault injection not working

**Cause**: Docker container not found or insufficient permissions

**Solution**:
```bash
# List containers
docker ps -a

# Verify container name
# Update container name in request if needed

# Check permissions
docker info  # Should not error
```

---

## Debugging Tips

### Enable verbose logging

```python
# In your Python files
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check service health

```bash
# Healing Dashboard
curl http://localhost:5001/api/health

# ML Model
curl http://localhost:8080/health

# Network Analyzer
curl http://localhost:8000/health
```

### Monitor all logs

```bash
# Watch all log files
tail -f logs/*.log

# Or use multitail
multitail logs/*.log
```

### Test individual components

```bash
# Test Gemini analyzer
python3 test_gemini_key.py

# Test dual AI switching
python3 test_ai_switching.py

# Test IP blocker
python3 -c "from monitoring.server.ip_blocker import IPBlocker; print('OK')"
```

---

## Getting Help

### Check Documentation

- [README.md](../README.md)
- [API Reference](API_REFERENCE.md)
- [Configuration Guide](guides/CONFIGURATION.md)
- [Feature Guides](features/)

### Debug Steps

1. Check logs: `tail -f logs/*.log`
2. Verify services are running: `ps aux | grep python`
3. Test API endpoints: `curl http://localhost:5001/api/health`
4. Check environment variables: `cat .env`
5. Verify dependencies: `pip list | grep -E "tensorflow|fastapi|groq"`

### Report Issues

When reporting issues, include:
- Error messages (full traceback)
- Service logs
- System info: `uname -a`, Python version
- Steps to reproduce
- Screenshot (if UI-related)

---

**Last Updated**: 2025-12-17  
**Version**: 2.0
