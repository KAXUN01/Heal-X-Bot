# 🔧 Heal-X-Bot: Docker Production Troubleshooting Guide

## Table of Contents

1. [Common Issues](#common-issues)
2. [Service-Specific Issues](#service-specific-issues)
3. [Network Issues](#network-issues)
4. [Resource Issues](#resource-issues)
5. [Database Issues](#database-issues)
6. [Security Issues](#security-issues)
7. [Performance Issues](#performance-issues)
8. [Recovery Procedures](#recovery-procedures)

---

## Common Issues

### Services Won't Start

**Symptoms:**
- Containers exit immediately
- `docker-compose ps` shows "Exited" status
- Error messages in logs

**Solutions:**

```bash
# Check logs
cd docker/production
docker-compose -f docker-compose.prod.yml logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs healing-dashboard

# Check container status
docker ps -a

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

**Common Causes:**
- Missing environment variables
- Port conflicts
- Insufficient resources
- Configuration errors

### Port Already in Use

**Symptoms:**
- Error: "port is already allocated"
- Services fail to start

**Solutions:**

```bash
# Find process using port
sudo lsof -i :5001
sudo netstat -tulpn | grep 5001

# Kill process
sudo kill -9 <PID>

# Or change port in .env.production
HEALING_DASHBOARD_PORT=5002
```

### Images Won't Build

**Symptoms:**
- Build fails with errors
- Dependencies not found

**Solutions:**

```bash
# Clean build
docker-compose -f docker-compose.prod.yml build --no-cache

# Check Dockerfile syntax
docker build -t test -f model/Dockerfile.prod model/

# Check disk space
df -h

# Clean Docker system
docker system prune -a
```

### Environment Variables Not Loading

**Symptoms:**
- Services start but can't connect
- API keys not working

**Solutions:**

```bash
# Verify .env file exists
ls -la docker/production/.env.production

# Check file permissions
chmod 600 docker/production/.env.production

# Verify variables are loaded
docker-compose -f docker-compose.prod.yml --env-file .env.production config

# Check in container
docker exec heal-x-bot-dashboard env | grep GEMINI
```

---

## Service-Specific Issues

### Model API Issues

**Symptoms:**
- Model not loading
- Predictions failing
- High latency

**Solutions:**

```bash
# Check model file exists
ls -la model/ddos_model.keras

# Check model API logs
docker-compose -f docker-compose.prod.yml logs model

# Test model API
curl http://localhost:8080/health

# Rebuild model service
docker-compose -f docker-compose.prod.yml build model
docker-compose -f docker-compose.prod.yml up -d model
```

**Common Issues:**
- Model file missing or corrupted
- Insufficient memory for TensorFlow
- Model version mismatch

### Dashboard Not Loading

**Symptoms:**
- Dashboard returns 502/503 errors
- WebSocket connections fail
- Static files not loading

**Solutions:**

```bash
# Check dashboard logs
docker-compose -f docker-compose.prod.yml logs healing-dashboard

# Check service dependencies
docker-compose -f docker-compose.prod.yml ps

# Verify volumes mounted
docker inspect heal-x-bot-dashboard | grep Mounts

# Restart dashboard
docker-compose -f docker-compose.prod.yml restart healing-dashboard
```

### Monitoring Server Issues

**Symptoms:**
- Metrics not updating
- Health checks failing
- High CPU usage

**Solutions:**

```bash
# Check monitoring logs
docker-compose -f docker-compose.prod.yml logs server

# Check resource usage
docker stats heal-x-bot-monitoring

# Verify model API connection
docker exec heal-x-bot-monitoring curl http://model:8080/health

# Restart monitoring
docker-compose -f docker-compose.prod.yml restart server
```

### Incident Bot Issues

**Symptoms:**
- AI analysis not working
- API errors
- Timeout errors

**Solutions:**

```bash
# Check incident bot logs
docker-compose -f docker-compose.prod.yml logs incident-bot

# Verify API keys
docker exec heal-x-bot-incident-bot env | grep GEMINI

# Test API connection
curl http://localhost:8001/health

# Check model API connectivity
docker exec heal-x-bot-incident-bot curl http://model:8080/health
```

---

## Network Issues

### Services Can't Communicate

**Symptoms:**
- Connection refused errors
- Timeout errors
- Services can't reach each other

**Solutions:**

```bash
# Check network
docker network ls
docker network inspect heal-x-bot_healing-network

# Test connectivity between containers
docker exec heal-x-bot-dashboard ping model
docker exec heal-x-bot-dashboard curl http://model:8080/health

# Recreate network
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### External Access Issues

**Symptoms:**
- Can't access from outside server
- Connection timeout
- 502 Bad Gateway

**Solutions:**

```bash
# Check firewall
sudo ufw status
sudo ufw allow 5001/tcp

# Check port binding
docker-compose -f docker-compose.prod.yml ps
netstat -tulpn | grep 5001

# Check Nginx (if using)
sudo nginx -t
sudo systemctl status nginx
```

---

## Resource Issues

### Out of Memory

**Symptoms:**
- Containers killed (OOM)
- Services crash
- System slow

**Solutions:**

```bash
# Check memory usage
free -h
docker stats

# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Reduce resource limits in docker-compose.prod.yml
# Or add more RAM to server
```

### High CPU Usage

**Symptoms:**
- System slow
- Services unresponsive
- High load average

**Solutions:**

```bash
# Check CPU usage
top
docker stats

# Identify resource hogs
docker stats --no-stream

# Adjust CPU limits in docker-compose.prod.yml
# Scale services if needed
```

### Disk Space Full

**Symptoms:**
- Build fails
- Services can't write logs
- Docker errors

**Solutions:**

```bash
# Check disk space
df -h
du -sh /var/lib/docker

# Clean Docker
docker system prune -a
docker volume prune

# Clean old logs
docker-compose -f docker-compose.prod.yml logs --tail=0

# Remove old images
docker image prune -a
```

---

## Database Issues

### Database Corruption

**Symptoms:**
- Database errors
- Services can't read/write
- SQLite errors

**Solutions:**

```bash
# Backup first
cd docker/scripts
./backup.sh

# Check database file
docker exec heal-x-bot-dashboard ls -la /app/data/

# Verify database
docker exec heal-x-bot-dashboard sqlite3 /app/data/blocked_ips.db "PRAGMA integrity_check;"

# Restore from backup if corrupted
./restore.sh <backup-name>
```

### Database Locked

**Symptoms:**
- "database is locked" errors
- Write operations fail

**Solutions:**

```bash
# Check for multiple connections
docker-compose -f docker-compose.prod.yml ps

# Restart services to release locks
docker-compose -f docker-compose.prod.yml restart

# Check database file permissions
docker exec heal-x-bot-dashboard ls -la /app/data/
```

---

## Security Issues

### Unauthorized Access

**Symptoms:**
- Unknown IPs accessing services
- Unusual activity in logs

**Solutions:**

```bash
# Check access logs
docker-compose -f docker-compose.prod.yml logs | grep -i "unauthorized"

# Review firewall rules
sudo ufw status verbose

# Check blocked IPs
docker exec heal-x-bot-dashboard sqlite3 /app/data/blocked_ips.db "SELECT * FROM blocked_ips;"

# Enable rate limiting in Nginx
# Review nginx.conf
```

### API Key Leakage

**Symptoms:**
- API keys in logs
- Unauthorized API usage

**Solutions:**

```bash
# Check logs for keys
docker-compose -f docker-compose.prod.yml logs | grep -i "api_key"

# Rotate API keys immediately
# Update .env.production
# Restart services

# Review .env file permissions
chmod 600 docker/production/.env.production
```

---

## Performance Issues

### Slow Response Times

**Symptoms:**
- High latency
- Timeout errors
- Slow dashboard

**Solutions:**

```bash
# Check resource usage
docker stats

# Check network latency
docker exec heal-x-bot-dashboard ping model

# Review logs for errors
docker-compose -f docker-compose.prod.yml logs | grep -i error

# Optimize resource limits
# Increase CPU/memory in docker-compose.prod.yml
```

### High Memory Usage

**Symptoms:**
- Memory usage > 80%
- Services restarting

**Solutions:**

```bash
# Check memory usage per service
docker stats --no-stream

# Identify memory leaks
docker-compose -f docker-compose.prod.yml logs | grep -i "memory"

# Adjust memory limits
# Restart services
docker-compose -f docker-compose.prod.yml restart
```

---

## Recovery Procedures

### Complete Service Failure

**Symptoms:**
- All services down
- Can't access dashboard

**Solutions:**

```bash
# Stop all services
cd docker/production
docker-compose -f docker-compose.prod.yml down

# Check system resources
free -h
df -h

# Restart Docker daemon (if needed)
sudo systemctl restart docker

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify
./scripts/health-check.sh
```

### Data Loss Recovery

**Symptoms:**
- Data missing
- Database empty
- Configuration lost

**Solutions:**

```bash
# List available backups
cd docker/scripts
./restore.sh --list

# Restore from backup
./restore.sh <backup-name>

# Verify data restored
docker exec heal-x-bot-dashboard sqlite3 /app/data/blocked_ips.db "SELECT COUNT(*) FROM blocked_ips;"
```

### Rollback Deployment

**Symptoms:**
- New deployment has issues
- Need to revert

**Solutions:**

```bash
# List backups
cd docker/scripts
./restore.sh --list

# Rollback
./rollback.sh <backup-name>

# Or manually
cd docker/production
docker-compose -f docker-compose.prod.yml down
# Restore previous images/config
docker-compose -f docker-compose.prod.yml up -d
```

---

## Diagnostic Commands

### System Information

```bash
# Docker version
docker --version
docker-compose --version

# System resources
free -h
df -h
top

# Docker system info
docker system df
docker system info
```

### Service Information

```bash
# Service status
cd docker/production
docker-compose -f docker-compose.prod.yml ps

# Service logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Resource usage
docker stats --no-stream

# Network information
docker network inspect heal-x-bot_healing-network
```

### Container Inspection

```bash
# Inspect container
docker inspect heal-x-bot-dashboard

# Container logs
docker logs heal-x-bot-dashboard --tail=100 -f

# Execute commands in container
docker exec -it heal-x-bot-dashboard bash
docker exec heal-x-bot-dashboard env
```

---

## Getting Help

### Log Collection

```bash
# Collect all logs
cd docker/production
docker-compose -f docker-compose.prod.yml logs > /tmp/healx-logs.txt

# System information
docker system info > /tmp/docker-info.txt
docker stats --no-stream > /tmp/docker-stats.txt

# Service status
docker-compose -f docker-compose.prod.yml ps > /tmp/service-status.txt
```

### Support Resources

- Check documentation: `docs/deployment/DOCKER_PRODUCTION_GUIDE.md`
- Review logs: `docker-compose logs`
- Check GitHub issues
- Review health check output: `./scripts/health-check.sh`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Maintained By**: Heal-X-Bot Development Team

