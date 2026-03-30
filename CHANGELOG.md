# Changelog

All notable changes to Heal-X-Bot are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-17

### Added - Major Features
- **Dual AI Provider Support**: Gemini (primary) + Groq (fallback) for log analysis
  - Automatic provider selection based on API keys
  - Gemini `gemini-2.5-flash-lite-preview-09-2025` model
  - Groq `llama-3.3-70b-versatile` model as fallback
- **Cloud Simulation & Fault Injection**: Test auto-healing with controlled faults
  - Service crash simulation
  - CPU spike, memory leak, disk full, network issue injection
  - Automated fault detection
  - Container healing capabilities
- **Enhanced API Documentation**: Comprehensive API reference for all 4 services (50+ endpoints)
- **Real-time WebSocket Events**: Live dashboard updates via WebSocket connections
- **Service Discovery**: Automatic detection of Docker, systemd, and Kubernetes services
- **Integrated Terminal**: CLI terminal within healing dashboard

### Added - Documentation
- `docs/API_REFERENCE.md`: Complete API catalog for all services
- `docs/features/AI_LOG_ANALYSIS.md`: Deep dive into dual AI provider system
- `docs/TROUBLESHOOTING.md`: 30+ common issues with solutions
- Reorganized documentation structure with `/docs/features/`, `/docs/api/`, `/docs/architecture/`
- Archived 50+ redundant docs to `/docs/legacy/`

### Changed
- **Primary AI Provider**: Gemini now preferred over Groq
- **Architecture**: Healing Dashboard (port 5001) is now primary UI
- **Environment Config**: Added `GEMINI_API_KEY` as primary, `GROQ_API_KEY` as fallback
- **Discord**: Replaced Slack as recommended notification platform
- **README**: Updated with all current features and accurate architecture diagram
- **Port Configuration**: Clarified port assignments across all services

### Improved
- AI log analysis response format (3-section: What/How/Prevention)
- System monitoring with 13 critical services tracked
- Auto-healing orchestration with modular actions
- IP blocking with comprehensive statistics tracking
- Log management with automatic rotation (10MB limit)
- Error handling across all API endpoints

### Fixed
- Gemini AI library installation (`google-generativeai>=0.3.0`)
- API key detection and validation for both providers
- Provider initialization logic in `healing_dashboard_api.py` and `app.py`
- Port conflicts documentation
- Service startup dependencies

## [1.5.0] - 2025-12-15

### Added
- Predictive Maintenance with XGBoost models
- Failure prediction 1-24 hours before occurrence
- Time-to-failure estimation
- Early warning system integration

### Changed
- Enhanced DDoS detection model accuracy
- Improved ML model monitoring

## [1.4.0] - 2025-12-14

### Added
- DDoS simulation and metrics
- ML performance metrics to dashboard
- Unified healing dashboard combining ML + system monitoring

### Fixed
- Dashboard metrics not updating during DDoS simulation
- ML metrics integration issues

## [1.3.0] - 2025-12-13

### Added
- Modular auto-healing system
- Healing action modules (system, container, resource)
- Healing verification and history tracking

### Changed
- Reorganized healing code structure
- Centralized configuration management

### Fixed
- Multiple bugs in healing orchestrator
- Security vulnerabilities in monitoring server

## [1.2.0] - 2025-11-XX

### Added
- Critical services monitoring (13 services)
- System-wide log collection (Docker, systemd, journalctl)
- Anomaly detection with multi-source fallback
- Health scoring system

### Changed
- Log rotation policies (10MB limit)
- Monitoring intervals (30 seconds for critical services)

## [1.1.0] - 2025-10-XX

### Added
- IP blocking database (SQLite)
- Automatic IP blocking on high threat (≥80%)
- Manual IP management interface
- Blocking statistics and analytics

### Changed
- IP blocker persistence layer
- Dashboard IP management UI

## [1.0.0] - 2025-09-XX

### Added - Initial Release
- DDoS detection with TensorFlow
- Real-time threat level assessment
- Attack pattern recognition (HTTP Flood, SYN Flood, Bot Activity)
- Basic monitoring dashboard
- Prometheus metrics integration
- Network analyzer service
- ML model API
- Flask monitoring server

---

## Version History Summary

- **2.0.0** (2025-12-17): Dual AI providers, cloud simulation, comprehensive docs
- **1.5.0** (2025-12-15): Predictive maintenance
- **1.4.0** (2025-12-14): DDoS simulation, unified dashboard
- **1.3.0** (2025-12-13): Modular auto-healing
- **1.2.0** (2025-11-XX): Critical services monitoring
- **1.1.0** (2025-10-XX): IP blocking system
- **1.0.0** (2025-09-XX): Initial release

---

## Deprecated Features

### Removed in 2.0.0
- Single AI provider limitation (now supports both Gemini and Groq)
- Groq-only configuration
- Slack as primary notification (moved to Discord)

---

## Upgrade Guide

### 1.x → 2.0

1. **API Keys**: Add Gemini key to `.env`:
   ```bash
   echo "GEMINI_API_KEY=your_key_here" >> .env
   ```

2. **Install Dependencies**:
   ```bash
   pip install google-generativeai>=0.3.0
   ```

3. **Restart Services**:
   ```bash
   ./start.sh restart
   ```

4. **Verify**:
   ```bash
   curl http://localhost:5001/api/gemini/status
   # Should show "analyzer_type": "gemini"
   ```

---

## Breaking Changes

### 2.0.0
- Environment variable `GOOGLE_API_KEY` deprecated in favor of `GEMINI_API_KEY`
- API endpoint `/api/groq/analyze-log` renamed to `/api/gemini/analyze-log` (works with both providers)
- Removed legacy `/api/slack/` endpoints (use `/api/discord/` instead)

---

For older changes and detailed fix history, see `/docs/legacy/changelog/`.

**Last Updated**: 2025-12-17
