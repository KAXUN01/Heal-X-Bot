# 🐳 Heal-X-Bot Docker Deployment

This directory contains Docker configurations and scripts for deploying Heal-X-Bot in production and development environments.

## Directory Structure

```
docker/
├── production/              # Production deployment files
│   ├── docker-compose.prod.yml    # Production Docker Compose
│   ├── env.production.template    # Production environment template
│   └── nginx.conf                 # Nginx reverse proxy config
├── development/             # Development deployment files
│   └── env.development.template   # Development environment template
└── scripts/                 # Deployment automation scripts
    ├── deploy.sh           # Initial deployment
    ├── update.sh           # Update existing deployment
    ├── rollback.sh         # Rollback to previous version
    ├── backup.sh           # Create backup
    ├── restore.sh          # Restore from backup
    └── health-check.sh     # Health check all services
```

## Quick Start

### Production Deployment

```bash
# 1. Configure environment
cd docker/production
cp env.production.template .env.production
nano .env.production  # Edit with your values

# 2. Deploy
cd ../scripts
./deploy.sh

# 3. Verify
./health-check.sh
```

### Development Deployment

```bash
# 1. Configure environment
cd docker/development
cp env.development.template .env.development
nano .env.development  # Edit with your values

# 2. Deploy
cd ../../config
docker-compose -f docker-compose.yml up -d
```

## Services

The production deployment includes:

- **model**: DDoS detection ML model API (Port 8080)
- **server**: Monitoring server (Port 5000)
- **healing-dashboard**: Main dashboard API (Port 5001)
- **incident-bot**: AI incident response bot (Port 8001)
- **prometheus**: Metrics collection (Port 9090)

## Scripts

### deploy.sh
Initial deployment script that:
- Checks prerequisites
- Creates backup
- Builds images
- Deploys services
- Verifies health

### update.sh
Update script for:
- Pulling latest code
- Building new images
- Rolling update
- Health verification

### rollback.sh
Rollback script for:
- Listing backups
- Restoring previous version
- Starting services

### backup.sh
Backup script that:
- Backs up volumes
- Backs up configuration
- Backs up databases
- Compresses backup

### restore.sh
Restore script for:
- Listing backups
- Restoring volumes
- Restoring configuration
- Starting services

### health-check.sh
Health check script that:
- Checks all containers
- Tests all endpoints
- Shows resource usage
- Reports status

## Documentation

- **Production Guide**: `docs/deployment/DOCKER_PRODUCTION_GUIDE.md`
- **Deployment Checklist**: `docs/deployment/DEPLOYMENT_CHECKLIST.md`
- **Troubleshooting**: `docs/deployment/TROUBLESHOOTING.md`

## Environment Files

### Production (.env.production)

Required variables:
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_API_KEY`: Google API key
- `DISCORD_WEBHOOK`: Discord webhook URL (recommended)

Optional variables:
- Port configurations
- Resource limits
- Backup settings

### Development (.env.development)

Similar to production but with:
- More verbose logging (DEBUG)
- Relaxed security
- Lower resource limits

## Docker Compose Files

### Production (docker-compose.prod.yml)

Features:
- Multi-stage builds
- Resource limits
- Security hardening
- Health checks
- Auto-restart
- Log rotation

### Development (config/docker-compose.yml)

Features:
- Faster builds
- Development settings
- Hot reload support

## Best Practices

1. **Always backup before updates**
2. **Test in development first**
3. **Monitor resource usage**
4. **Keep environment files secure**
5. **Regular security updates**
6. **Monitor logs regularly**
7. **Test backup/restore procedures**

## Support

For issues:
1. Check `docs/deployment/TROUBLESHOOTING.md`
2. Review logs: `docker-compose logs`
3. Run health check: `./scripts/health-check.sh`
4. Check GitHub issues

---

**Last Updated**: 2025-01-19

