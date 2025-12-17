# 🚀 Startup Guide

This guide explains how to start the Healing-Bot application.

## Quick Start

### Option 1: Using the Startup Script (Recommended)

```bash
./start.sh
```

This script will:
- ✅ Check Python version (requires 3.8+)
- ✅ Check project structure
- ✅ Check port availability
- ✅ Activate virtual environment if available
- ✅ Create .env file from template if needed
- ✅ Start all services

### Option 2: Using the Python Launcher Directly

```bash
python3 run-healing-bot.py
```

Or with specific options:

```bash
# Auto-detect mode (Docker or native)
python3 run-healing-bot.py --mode auto

# Force native Python mode
python3 run-healing-bot.py --mode native

# Force Docker mode
python3 run-healing-bot.py --mode docker

# Start specific services only
python3 run-healing-bot.py --services model dashboard healing-dashboard

# Setup only (don't start services)
python3 run-healing-bot.py --setup-only
```

## Services Started

The application starts the following services:

1. **Model API** (Port 8080) - DDoS detection model
2. **Network Analyzer** (Port 8000) - Network traffic analysis
3. **Dashboard** (Port 3001) - Main monitoring dashboard
4. **Incident Bot** (Port 8000) - AI incident response
5. **Monitoring Server** (Port 5000) - System metrics
6. **Healing Dashboard API** (Port 5001) - Healing bot dashboard

## Access Points

Once started, access the services at:

- **📊 Dashboard**: http://localhost:3001
- **🛡️ Healing Dashboard**: http://localhost:5001
- **🤖 Model API**: http://localhost:8080
- **🔍 Network Analyzer**: http://localhost:8000
- **🚨 Incident Bot**: http://localhost:8000
- **📈 Monitoring Server**: http://localhost:5000

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Required Python packages (installed automatically)

## Troubleshooting

### Port Already in Use

If a port is already in use, you can:
1. Stop the process using that port
2. Or modify the port in the service configuration

### Missing Dependencies

The launcher will automatically try to install missing dependencies. If installation fails:
1. Check your internet connection
2. Try installing manually: `pip install -r requirements.txt`
3. Check Python version: `python3 --version`

### Services Not Starting

1. Check the error messages in the console
2. Verify all required directories exist
3. Check that .env file is configured (if needed)
4. Ensure ports are available

### Virtual Environment

If you have a virtual environment:
- The startup script will automatically activate it
- Or activate manually: `source venv/bin/activate`

## Stopping the Application

Press `Ctrl+C` to stop all services gracefully.

The launcher will:
- Stop all running processes
- Clean up resources
- Exit cleanly

## Advanced Usage

### Custom Service Selection

Start only specific services:

```bash
python3 run-healing-bot.py --services model healing-dashboard
```

### Docker Mode

If Docker is available, the launcher can use Docker Compose:

```bash
python3 run-healing-bot.py --mode docker
```

### Setup Only

Just setup the environment without starting services:

```bash
python3 run-healing-bot.py --setup-only
```

## Environment Variables

Create a `.env` file in the project root (or copy from `config/env.template`):

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Discord Integration
DISCORD_WEBHOOK=your_discord_webhook_url_here

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

## Logs

Service logs are displayed in the console. For more detailed logs, check:
- Service-specific log files
- System logs
- Application logs in `logs/` directory

## Support

For issues or questions:
1. Check the main README.md
2. Review the documentation in `docs/`
3. Check service-specific logs
4. Verify all prerequisites are met

