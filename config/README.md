# ⚙️ Healing-Bot Configuration

Configuration files and templates for the Healing-Bot system.

---

## 📁 Files in This Directory

| File | Purpose | Type |
|------|---------|------|
| **env.template** | Environment variables template | Template |
| **docker-compose.yml** | Docker services configuration | Docker |
| **log_config.json** | Log management settings | JSON |
| **grafana.json** | Grafana dashboard template | JSON |

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy template to .env
cp config/env.template .env

# Edit with your values
nano .env
```

### 2. Docker Setup

```bash
# Start all services
docker-compose -f config/docker-compose.yml up -d

# View logs
docker-compose -f config/docker-compose.yml logs -f
```

---

## 📝 Configuration Files

### env.template

Environment variables template for the application.

**Categories:**
- **AI Configuration** - Gemini API keys
- **Slack Integration** - Slack bot tokens
- **AWS Configuration** - S3 credentials
- **Grafana Settings** - Dashboard auth
- **Port Configuration** - Service ports

**Usage:**
```bash
# 1. Copy template
cp config/env.template .env

# 2. Required variables
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# 3. Optional variables
SLACK_BOT_TOKEN=your_slack_token (if using Slack)
AWS_ACCESS_KEY_ID=your_aws_key (if using S3)
```

**Environment Variables:**

```bash
# AI Configuration
GEMINI_API_KEY=         # Get from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=         # Alternative key

# Slack (Optional)
SLACK_BOT_TOKEN=        # Slack bot OAuth token
SLACK_CHANNEL=          # Channel for notifications

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=      # AWS access key
AWS_SECRET_ACCESS_KEY=  # AWS secret key
AWS_REGION=us-east-1    # AWS region

# Ports
MONITORING_PORT=5000    # Monitoring server port
DASHBOARD_PORT=3001     # Dashboard port
PROMETHEUS_PORT=9090    # Prometheus port
```

---

### docker-compose.yml

Docker Compose configuration for multi-service deployment.

**Services:**
- **incident-bot** - Incident response automation (port 8000)
- **model** - ML model API (port 8080)
- **server** - Monitoring server (port 5000)
- **prometheus** - Metrics collection (port 9090)
- **dashboard** - Web dashboard (port 3001)

**Usage:**
```bash
# Start all services
docker-compose -f config/docker-compose.yml up -d

# Start specific service
docker-compose -f config/docker-compose.yml up -d dashboard

# View logs
docker-compose -f config/docker-compose.yml logs -f service_name

# Stop all services
docker-compose -f config/docker-compose.yml down
```

**Service Ports:**
- **8000** - Incident Bot
- **8080** - ML Model API
- **5000** - Monitoring Server (API-only)
- **3001** - Dashboard (Main UI)
- **9090** - Prometheus

---

### log_config.json

Log management and rotation configuration.

**Settings:**

```json
{
  "log_rotation": {
    "enabled": true,
    "max_size_mb": 10,
    "backup_count": 3,
    "compress": true,
    "delete_after_days": 7
  },
  "system_log_collector": {
    "max_logs_in_memory": 1000,
    "collection_interval_seconds": 30,
    "docker_tail_lines": 10,
    "systemd_tail_entries": 20
  }
}
```

**Configuration Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `max_size_mb` | 10 | Maximum log file size before rotation |
| `backup_count` | 3 | Number of backup files to keep |
| `compress` | true | Compress rotated logs (gzip) |
| `delete_after_days` | 7 | Delete logs older than N days |
| `max_logs_in_memory` | 1000 | Max logs to keep in memory |
| `collection_interval_seconds` | 30 | Log collection frequency |

**Usage:**
```python
import json

with open('config/log_config.json') as f:
    config = json.load(f)

max_size = config['log_rotation']['max_size_mb']
```

---

### grafana.json

Grafana dashboard template.

**Features:**
- Pre-configured panels
- Prometheus data source
- Custom metrics
- Alert rules

**Import:**
```bash
# Via UI
1. Open Grafana (http://localhost:3000)
2. Go to Dashboards > Import
3. Upload config/grafana.json

# Via API
curl -X POST \
  -H "Content-Type: application/json" \
  -d @config/grafana.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

---

## 🔒 Security Best Practices

### Environment Variables

1. **Never commit `.env`** to git
2. **Use strong passwords** for services
3. **Rotate API keys** regularly
4. **Limit API key scopes** to minimum required

### Docker Security

1. **Don't run as root** inside containers
2. **Use secrets** for sensitive data
3. **Limit network exposure** (only expose necessary ports)
4. **Keep images updated**

### File Permissions

```bash
# Restrict .env file
chmod 600 .env

# Restrict config files
chmod 644 config/*.json

# Executable scripts only
chmod 755 scripts/*.sh
```

---

## 🔧 Configuration Validation

### Validate Environment

```bash
# Check required variables
python scripts/setup/setup_env.py --validate

# Or manually
[ -z "$GEMINI_API_KEY" ] && echo "GEMINI_API_KEY not set"
```

### Validate Docker Compose

```bash
# Validate syntax
docker-compose -f config/docker-compose.yml config

# Check for errors
docker-compose -f config/docker-compose.yml config --quiet
echo $?  # Should return 0
```

### Validate JSON Files

```bash
# Validate log_config.json
python -m json.tool config/log_config.json

# Validate grafana.json
python -m json.tool config/grafana.json
```

---

## 📝 Environment-Specific Configurations

### Development

```bash
# Create dev environment
cp config/env.template .env.development

# Edit for dev
nano .env.development

# Use dev config
export $(cat .env.development | xargs)
```

### Production

```bash
# Create prod environment
cp config/env.template .env.production

# Secure prod config
chmod 600 .env.production

# Use prod config
export $(cat .env.production | xargs)
```

### Testing

```bash
# Create test environment
cp config/env.template .env.test

# Use test database
TEST_DB=true

# Load test config
export $(cat .env.test | xargs)
```

---

## 🔍 Troubleshooting

### Environment Variables Not Loading

```bash
# Check if .env exists
ls -la .env

# Manually load
export $(grep -v '^#' .env | xargs)

# Verify loaded
echo $GEMINI_API_KEY
```

### Docker Compose Errors

```bash
# Check syntax
docker-compose -f config/docker-compose.yml config

# Check service definitions
docker-compose -f config/docker-compose.yml ps

# View service logs
docker-compose -f config/docker-compose.yml logs service_name
```

### Port Conflicts

```bash
# Check what's using port
lsof -i:5000

# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Changed from 5000:5000
```

---

## 📚 Related Documentation

- **Environment Setup** - `../docs/guides/ENV_SETUP_GUIDE.md`
- **Deployment Guide** - `../docs/guides/UBUNTU_DEPLOYMENT_GUIDE.md`
- **Docker Guide** - Docker Compose documentation

---

## 🤝 Contributing

When updating configurations:

1. **Document all changes** in this README
2. **Update templates** (env.template, etc.)
3. **Validate syntax** before committing
4. **Test in dev environment** first
5. **Never commit secrets** (.env, keys, etc.)

---

**Last Updated:** October 29, 2025  
**Configuration Files:** 6  
**Status:** ✅ Production Ready

