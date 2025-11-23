# 🚀 Heal-X-Bot Deployment Scripts

This directory contains automation scripts for deploying and managing Heal-X-Bot in production.

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `deploy.sh` | Initial deployment | `./deploy.sh` |
| `update.sh` | Update deployment | `./update.sh` |
| `rollback.sh` | Rollback deployment | `./rollback.sh [backup-name]` |
| `backup.sh` | Create backup | `./backup.sh` |
| `restore.sh` | Restore backup | `./restore.sh [backup-name]` |
| `health-check.sh` | Health check | `./health-check.sh` |

## Usage Examples

### Initial Deployment

```bash
# Configure environment first
cd ../production
cp env.production.template .env.production
nano .env.production

# Deploy
cd ../scripts
./deploy.sh
```

### Update Deployment

```bash
# Pull latest code and update
./update.sh
```

### Create Backup

```bash
# Manual backup
./backup.sh

# Automated backup (add to crontab)
0 2 * * * /path/to/docker/scripts/backup.sh
```

### Restore Backup

```bash
# List available backups
./restore.sh --list

# Restore specific backup
./restore.sh 20250119_120000
```

### Health Check

```bash
# Check all services
./health-check.sh
```

### Rollback

```bash
# List backups
./rollback.sh --list

# Rollback to backup
./rollback.sh 20250119_120000
```

## Script Details

### deploy.sh

**What it does:**
1. Checks prerequisites (Docker, Docker Compose)
2. Verifies environment file exists
3. Creates backup of existing deployment
4. Builds Docker images
5. Deploys all services
6. Waits for health checks
7. Shows deployment status

**Requirements:**
- Docker installed
- Docker Compose installed
- `.env.production` file configured

### update.sh

**What it does:**
1. Pulls latest code
2. Creates backup
3. Builds new images
4. Performs rolling update
5. Verifies deployment

**Features:**
- Zero-downtime updates
- Service-by-service update
- Automatic health verification

### rollback.sh

**What it does:**
1. Lists available backups
2. Stops current services
3. Restores backup
4. Restores images
5. Starts services

**Usage:**
```bash
./rollback.sh --list          # List backups
./rollback.sh <backup-name>   # Rollback
```

### backup.sh

**What it backs up:**
- Docker volumes (healing-data, prometheus-data, model-cache)
- Configuration files (.env.production, docker-compose.prod.yml)
- Model files (ddos_model.keras, artifacts)
- Database files (*.db)

**Output:**
- Compressed tar.gz file
- Backup manifest
- Automatic cleanup of old backups

### restore.sh

**What it restores:**
- Docker volumes
- Configuration files
- Model files
- Database files

**Usage:**
```bash
./restore.sh --list           # List backups
./restore.sh <backup-name>    # Restore
```

### health-check.sh

**What it checks:**
- Container status
- Service endpoints
- Resource usage
- Health check status

**Output:**
- Service status table
- Health check results
- Resource usage statistics

## Error Handling

All scripts include:
- Error checking (`set -euo pipefail`)
- Color-coded output
- Detailed error messages
- Exit codes for automation

## Logging

Scripts output:
- `[INFO]`: Informational messages (green)
- `[WARN]`: Warnings (yellow)
- `[ERROR]`: Errors (red)

## Automation

### Cron Jobs

**Daily Backup:**
```bash
0 2 * * * /opt/heal-x-bot/docker/scripts/backup.sh
```

**Health Check:**
```bash
*/5 * * * * /opt/heal-x-bot/docker/scripts/health-check.sh
```

### CI/CD Integration

Scripts can be integrated into CI/CD pipelines:
- Exit codes indicate success/failure
- Structured output for parsing
- Idempotent operations

## Troubleshooting

### Script Fails

1. Check prerequisites: Docker, Docker Compose installed
2. Check permissions: Scripts are executable (`chmod +x`)
3. Check environment: `.env.production` exists and configured
4. Check logs: Review script output for errors

### Backup Fails

1. Check disk space: `df -h`
2. Check permissions: Write access to backup directory
3. Check volumes: Volumes exist and accessible

### Restore Fails

1. Verify backup exists: `./restore.sh --list`
2. Check disk space: Enough space for restore
3. Stop services: Services must be stopped before restore

## Best Practices

1. **Always backup before updates**
2. **Test scripts in development first**
3. **Monitor script output**
4. **Keep backups secure**
5. **Regular backup testing**
6. **Document custom configurations**

---

**Last Updated**: 2025-01-19

