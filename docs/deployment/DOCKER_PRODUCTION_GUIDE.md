# 🐳 Heal-X-Bot: Docker Production Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Deployment](#detailed-deployment)
5. [Configuration](#configuration)
6. [Service Management](#service-management)
7. [Monitoring](#monitoring)
8. [Backup & Recovery](#backup--recovery)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for deploying Heal-X-Bot in production using Docker Compose. The production setup includes:

- ✅ Optimized multi-stage Docker builds
- ✅ Resource limits and security hardening
- ✅ Health checks and auto-restart
- ✅ Centralized logging
- ✅ Backup and restore procedures
- ✅ Nginx reverse proxy configuration

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 8GB+ (16GB+ recommended)
- **Disk**: 50GB+ free space (SSD recommended)
- **Network**: Internet connection for initial setup

### Software Requirements

- **Docker**: 20.10+
- **Docker Compose**: 2.0+ (or Docker Compose V2)
- **Git**: For cloning repository
- **curl**: For health checks

### Access Requirements

- Root or sudo access
- SSH access to server
- Domain name (optional, for SSL)

---

## Quick Start

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd Heal-X-Bot
```

### 3. Configure Environment

```bash
cd docker/production
cp env.production.template .env.production
nano .env.production  # Edit with your values
```

### 4. Deploy

```bash
# Run deployment script
./scripts/deploy.sh

# Or manually
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d
```

### 5. Verify

```bash
# Check health
./scripts/health-check.sh

# Or manually
curl http://localhost:5001/api/health
```

---

## Detailed Deployment

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git vim ufw

# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### Step 2: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (optional)
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

### Step 3: Clone and Configure

```bash
# Clone repository
git clone <repository-url> /opt/heal-x-bot
cd /opt/heal-x-bot

# Navigate to production directory
cd docker/production

# Create environment file
cp env.production.template .env.production

# Edit environment file
nano .env.production
```

**Required Configuration:**

```env
# AI Configuration (Required)
GEMINI_API_KEY=your_actual_key_here
GOOGLE_API_KEY=your_actual_key_here

# Notification (Recommended)
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook

# Ports (Optional - defaults work)
MODEL_PORT=8080
MONITORING_SERVER_PORT=5000
HEALING_DASHBOARD_PORT=5001
INCIDENT_BOT_PORT=8001
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
```

### Step 4: Deploy Services

**Using Deployment Script (Recommended):**

```bash
cd docker/scripts
./deploy.sh
```

**Manual Deployment:**

```bash
cd docker/production

# Build images
docker-compose -f docker-compose.prod.yml --env-file .env.production build

# Start services
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### Step 5: Verify Deployment

```bash
# Health check script
cd docker/scripts
./health-check.sh

# Or check manually
curl http://localhost:5001/api/health
curl http://localhost:8080/health
curl http://localhost:5000/health
```

---

## Configuration

### Environment Variables

See `env.production.template` for all available options.

**Key Variables:**

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `DISCORD_WEBHOOK` | Discord webhook URL | Recommended |
| `MODEL_PORT` | Model API port | No (default: 8080) |
| `HEALING_DASHBOARD_PORT` | Dashboard port | No (default: 5001) |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

### Resource Limits

Edit `docker-compose.prod.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Port Configuration

Change ports in `.env.production`:

```env
MODEL_PORT=8080
HEALING_DASHBOARD_PORT=5001
```

---

## Service Management

### Start Services

```bash
cd docker/production
docker-compose -f docker-compose.prod.yml --env-file .env.production start
```

### Stop Services

```bash
cd docker/production
docker-compose -f docker-compose.prod.yml --env-file .env.production stop
```

### Restart Services

```bash
cd docker/production
docker-compose -f docker-compose.prod.yml --env-file .env.production restart
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f healing-dashboard

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Update Services

```bash
cd docker/scripts
./update.sh
```

### Rollback

```bash
cd docker/scripts
./rollback.sh --list  # List available backups
./rollback.sh <backup-name>
```

---

## Monitoring

### Health Checks

```bash
# Automated health check
cd docker/scripts
./health-check.sh

# Manual checks
curl http://localhost:5001/api/health
curl http://localhost:8080/health
curl http://localhost:5000/health
```

### Service Status

```bash
cd docker/production
docker-compose -f docker-compose.prod.yml ps
```

### Resource Usage

```bash
docker stats
```

### Prometheus Metrics

Access Prometheus at: `http://localhost:9090`

---

## Backup & Recovery

### Create Backup

```bash
cd docker/scripts
./backup.sh
```

### List Backups

```bash
cd docker/scripts
./restore.sh --list
```

### Restore Backup

```bash
cd docker/scripts
./restore.sh <backup-name>
```

### Automated Backups

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /opt/heal-x-bot/docker/scripts/backup.sh
```

---

## Security

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSL/TLS Setup

**Using Let's Encrypt:**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

### Nginx Reverse Proxy

See `docker/production/nginx.conf` for configuration.

**Install Nginx:**

```bash
sudo apt install nginx

# Copy configuration
sudo cp docker/production/nginx.conf /etc/nginx/sites-available/heal-x-bot
sudo ln -s /etc/nginx/sites-available/heal-x-bot /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Access Control

- Restrict Prometheus access (IP whitelist or authentication)
- Use API keys for external access
- Enable rate limiting in Nginx
- Regular security updates

---

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check container status
docker ps -a

# Check resource usage
docker stats
```

### Port Conflicts

```bash
# Find process using port
sudo lsof -i :5001

# Kill process
sudo kill -9 <PID>
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Increase swap (if needed)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Database Issues

```bash
# Check database volume
docker volume inspect heal-x-bot_healing-data

# Backup before fixing
./scripts/backup.sh
```

### Network Issues

```bash
# Check network
docker network ls
docker network inspect heal-x-bot_healing-network

# Restart network
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Maintenance

### Regular Tasks

**Daily:**
- Check service health
- Review logs for errors
- Monitor resource usage

**Weekly:**
- Review backup status
- Check disk space
- Update dependencies

**Monthly:**
- Security updates
- Review and optimize configuration
- Test backup/restore procedures

### Updates

```bash
# Pull latest code
git pull

# Update services
cd docker/scripts
./update.sh
```

### Log Rotation

Docker handles log rotation automatically (configured in docker-compose.yml):
- Max size: 10MB per log file
- Max files: 5 files per service
- Compression: Enabled

---

## Next Steps

- Configure Nginx reverse proxy
- Set up SSL certificates
- Configure monitoring alerts
- Set up automated backups
- Review security settings

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Maintained By**: Heal-X-Bot Development Team

