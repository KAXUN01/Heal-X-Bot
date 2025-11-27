# Heal-X-Bot Services Status

## ✅ Fixed Issues

1. **Flask Configuration Error** - Fixed by setting `PROVIDE_AUTOMATIC_OPTIONS` config before Bootstrap initialization
2. **Protobuf Compatibility** - Fixed by ensuring protobuf >= 5.28.0, < 6.0.0 for TensorFlow 2.20.0 compatibility
3. **Log Directory Permissions** - Fixed by ensuring proper ownership and permissions

## 🚀 Startup Script

**File:** `start-all-services.sh`

This comprehensive script:
- ✅ Sets up virtual environment
- ✅ Installs all dependencies
- ✅ Fixes protobuf compatibility automatically
- ✅ Starts all services with proper error handling
- ✅ Monitors service health
- ✅ Provides graceful shutdown (Ctrl+C)

### Usage

```bash
./start-all-services.sh
```

## 📊 Service Status

| Service | Port | Status | Health Endpoint |
|---------|------|--------|----------------|
| **DDoS Model API** | 8080 | ✅ Running | http://localhost:8080/health |
| **Network Analyzer** | 8000 | ✅ Running | http://localhost:8000/health |
| **Healing Dashboard API** | 5001 | ✅ Running | http://localhost:5001/ |
| **Monitoring Server** | 5000 | ⚠️ Starting | http://localhost:5000/health |
| **Incident Bot** | 8001 | ⚠️ Starting | http://localhost:8001/health |

## 🌐 Access Points

- **🛡️ Healing Dashboard**: http://localhost:5001
- **🤖 DDoS Model API**: http://localhost:8080
- **🔍 Network Analyzer**: http://localhost:8000
- **🚨 Incident Bot**: http://localhost:8001
- **📈 Monitoring Server**: http://localhost:5000
- **📊 Fluent Bit**: http://localhost:8888 (if Docker is available)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root (template available at `config/env.template`):

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Discord Integration (optional)
DISCORD_WEBHOOK=your_discord_webhook_url_here

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

## 📝 Notes

- The startup script automatically handles dependency installation and compatibility fixes
- Services are started in the background with proper logging
- All logs are stored in the `logs/` directory
- PID files are stored in `.pids/` directory for process management
- Press Ctrl+C to gracefully stop all services

## 🐛 Troubleshooting

### Service Not Starting

1. Check logs: `tail -f logs/[Service Name].log`
2. Verify Python version: `python3 --version` (requires 3.8+)
3. Check port availability: `lsof -i :[port]`
4. Verify dependencies: `source .venv/bin/activate && pip list`

### Protobuf Issues

The script automatically fixes protobuf compatibility, but if issues persist:
```bash
source .venv/bin/activate
pip install --force-reinstall "protobuf>=5.28.0,<6.0.0"
```

### Permission Issues

If you encounter permission errors:
```bash
chmod -R 755 logs/ .pids/
```

## 📚 Additional Documentation

- Main README: `README.md`
- Quick Start Guide: `QUICK_START_MANAGED.md`
- Project Structure: `PROJECT_STRUCTURE.md`

