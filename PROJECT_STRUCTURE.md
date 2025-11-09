# 📁 Project Structure

This document provides an overview of the Heal-X-Bot project structure and organization.

## 📂 Root Directory

```
Heal-X-Bot/
├── README.md                 # Main project documentation
├── LICENSE                   # Project license
├── requirements.txt          # Python dependencies
├── setup.py                  # Project setup script
├── run-healing-bot.py        # Main launcher script
└── PROJECT_STRUCTURE.md      # This file
```

## 📂 Core Directories

### `config/`
Configuration files for Docker, Fluent Bit, and environment setup.
- `docker-compose.yml` - Main Docker Compose configuration
- `docker-compose-fluent-bit.yml` - Fluent Bit Docker configuration
- `env.template` - Environment variables template
- `fluent-bit/` - Fluent Bit configuration files
- `log_config.json` - Logging configuration

### `data/`
Data storage and exports.
- `exports/` - Exported data files (CSV, JSON, etc.)

### `docs/`
Project documentation.
- `guides/` - User guides and tutorials
- `changelog/` - Change logs and feature summaries
- `quick-reference/` - Quick reference materials
- `README.md` - Documentation index

### `incident-bot/`
AI-powered incident response bot.
- `main.py` - Main bot application
- `requirements.txt` - Bot dependencies
- `Dockerfile` - Docker configuration

### `model/`
Machine learning DDoS detection model.
- `main.py` - Model API server
- `ddos_detector.py` - DDoS detection logic
- `ddos_model/` - Trained model files
- `ddos_model_retrained/` - Retrained model files
- `requirements.txt` - Model dependencies
- `Dockerfile` - Docker configuration

### `monitoring/`
Monitoring and dashboard components.
- `dashboard/` - Web dashboard application
- `server/` - Monitoring server and API
- `prometheus/` - Prometheus configuration
- `alertmanager/` - Alertmanager configuration

### `scripts/`
Utility and deployment scripts.
- `deployment/` - Deployment scripts and service files
- `setup/` - Setup and installation scripts
- `testing/` - Testing and debugging scripts
- `maintenance/` - Maintenance and cleanup scripts
- `README.md` - Scripts documentation

### `tests/`
Test files and test utilities.
- `scripts/` - Test scripts (Python and Shell)
- `debug/` - Debug utilities
- `README.md` - Testing documentation

### `logs/`
Log files (gitignored, generated at runtime).
- `centralized/` - Centralized log files
- `fluent-bit/` - Fluent Bit output logs

### `infra/`
Infrastructure as code.
- `main.tofu` - Main Terraform/OpenTofu configuration
- `creates3user/` - S3 user creation scripts

## 🎯 Key Files

### Main Entry Points
- `run-healing-bot.py` - Unified launcher for all services
- `setup.py` - Project setup and dependency installation

### Configuration
- `config/docker-compose.yml` - Docker services configuration
- `config/env.template` - Environment variables template
- `.gitignore` - Git ignore rules

### Documentation
- `README.md` - Main project documentation
- `docs/guides/` - User guides and tutorials
- `docs/changelog/` - Feature changes and fixes

## 📋 Directory Purposes

### `config/`
Contains all configuration files needed to run the project. Never commit sensitive data here; use `env.template` as a reference.

### `data/`
Storage for exported data and temporary files. This directory may contain generated files.

### `docs/`
All project documentation. Guides are in `docs/guides/`, and changelogs are in `docs/changelog/`.

### `scripts/`
Organized by purpose:
- **deployment/** - Scripts for deploying the application
- **setup/** - Scripts for initial setup and installation
- **testing/** - Scripts for testing and generating test data
- **maintenance/** - Scripts for maintenance tasks

### `tests/`
Test files organized by type:
- **scripts/** - All test scripts (Python and Shell)
- **debug/** - Debug utilities and tools

### `logs/`
Runtime log files (gitignored). Contains application logs, centralized logs, and Fluent Bit output.

## 🚀 Getting Started

1. **Read the main README.md** for project overview
2. **Check docs/guides/** for detailed guides
3. **Use scripts/setup/** for installation
4. **Use scripts/deployment/** for deployment
5. **Use tests/scripts/** for testing

## 📝 Notes

- All test files are in `tests/scripts/` or `tests/debug/`
- All documentation is in `docs/`
- All scripts are in `scripts/` organized by purpose
- Configuration files are in `config/`
- Data exports are in `data/exports/`

## 🔍 Finding Files

- **Test files**: `tests/scripts/` or `tests/debug/`
- **Documentation**: `docs/guides/` or `docs/changelog/`
- **Scripts**: `scripts/` (organized by purpose)
- **Configuration**: `config/`
- **Models**: `model/`
- **Monitoring**: `monitoring/`

