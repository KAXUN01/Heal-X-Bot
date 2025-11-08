# Heal-X-Bot Repository Summary

## Overview
Heal-X-Bot is an intelligent system monitoring and log analysis platform with AI-powered insights, Fluent Bit integration, and comprehensive log management.

## Recent Updates (Latest Commit: ecd7225)

### 🐛 Major Fixes

#### 1. **Gemini AI API Client Fix**
- **Problem**: `module 'google.generativeai' has no attribute 'Client'`
- **Solution**: Updated to use `genai.configure()` and `genai.GenerativeModel()`
- **File**: `monitoring/server/gemini_log_analyzer.py`
- **Impact**: AI analysis now works correctly with Google Gemini API

#### 2. **Fluent Bit Container Fix**
- **Problem**: Container restarting with exit code 255
- **Solution**: Removed invalid `Format json_lines` parameter from file output plugin
- **File**: `config/fluent-bit/fluent-bit.conf`
- **Impact**: Fluent Bit now starts successfully and collects logs

#### 3. **Dashboard Error Handling**
- **Problem**: Poor error messages when Fluent Bit not available
- **Solution**: Enhanced error detection and user-friendly messages
- **Files**: `monitoring/server/healing_dashboard_api.py`, `monitoring/dashboard/static/healing-dashboard.html`
- **Impact**: Better user experience with actionable error messages

### ✨ New Features

#### 1. **AI Analysis for Fluent Bit Logs**
- Added AI analysis support for Fluent Bit log entries
- Individual log analysis with root cause, quick fix, and prevention
- Pattern analysis for multiple logs
- Works with both Fluent Bit and Centralized Logger

#### 2. **Enhanced Quick Analyze**
- Improved quick-analyze endpoint to work with both log sources
- Automatic fallback from Fluent Bit to Centralized Logger
- Better error handling and user feedback

#### 3. **Helper Scripts**
- `scripts/fix-fluent-bit.sh` - Fixes Fluent Bit container issues
- `scripts/diagnose-fluent-bit.sh` - Diagnoses Fluent Bit problems
- `scripts/pull-fluent-bit-image.sh` - Pulls Fluent Bit Docker image
- `scripts/start-fluent-bit-fixed.sh` - Starts Fluent Bit with fixed config
- `scripts/setup-git-auth.sh` - Helps set up Git authentication

## Repository Structure

### Core Components

#### 1. **Monitoring Server** (`monitoring/server/`)
- `healing_dashboard_api.py` - Main API server (FastAPI)
- `gemini_log_analyzer.py` - AI log analysis with Google Gemini
- `fluent_bit_reader.py` - Reads and parses Fluent Bit logs
- `centralized_logger.py` - Centralized log collection system
- `system_log_collector.py` - System-wide log collection
- `critical_services_monitor.py` - Monitors critical services

#### 2. **Dashboard** (`monitoring/dashboard/`)
- `static/healing-dashboard.html` - Main dashboard UI
- Features:
  - Real-time log viewing
  - AI-powered log analysis
  - Fluent Bit integration
  - Centralized Logger support
  - Error and warning filtering
  - Service-based filtering

#### 3. **Fluent Bit Configuration** (`config/fluent-bit/`)
- `fluent-bit.conf` - Fluent Bit configuration
- `parsers.conf` - Log parsers configuration
- `docker-compose-fluent-bit.yml` - Docker Compose setup

#### 4. **Scripts** (`scripts/`)
- `start-fluent-bit.sh` - Start Fluent Bit container
- `fix-fluent-bit.sh` - Fix Fluent Bit issues
- `diagnose-fluent-bit.sh` - Diagnose Fluent Bit problems
- `pull-fluent-bit-image.sh` - Pull Docker image
- `setup-git-auth.sh` - Git authentication helper

### Documentation Files

1. **AI_ANALYSIS_FLUENT_BIT.md** - AI analysis feature documentation
2. **FIXES_APPLIED.md** - Summary of all fixes applied
3. **FLUENT_BIT_DASHBOARD_FIX.md** - Dashboard fix documentation
4. **FLUENT_BIT_FIX.md** - Fluent Bit troubleshooting guide
5. **FLUENT_BIT_FORMAT_FIX.md** - Format fix documentation
6. **QUICK_START_FLUENT_BIT.md** - Quick start guide
7. **START_FLUENT_BIT_COMPLETE.md** - Complete setup guide
8. **START_FLUENT_BIT_INSTRUCTIONS.md** - Setup instructions
9. **GITHUB_PUSH_GUIDE.md** - GitHub push instructions
10. **REPOSITORY_SUMMARY.md** - This file

## Key Features

### 1. **Log Management**
- **Fluent Bit Integration**: Collects logs from syslog, kernel, auth, and systemd
- **Centralized Logger**: Python-based log collection system
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Filtering**: By service, level, source, and search text
- **Pagination**: Efficient handling of large log volumes

### 2. **AI-Powered Analysis**
- **Individual Log Analysis**: Root cause, quick fix, prevention
- **Pattern Analysis**: Identifies common issues and correlations
- **Service Health Analysis**: Overall service health assessment
- **Google Gemini Integration**: Uses Gemini 2.0 Flash model

### 3. **Dashboard Features**
- **Multi-source Logs**: Fluent Bit and Centralized Logger
- **Visual Statistics**: Total logs, services, errors, warnings
- **Interactive UI**: Modern, responsive design
- **Error Highlighting**: Color-coded log levels
- **AI Analysis Panel**: Dedicated panel for AI insights

### 4. **System Monitoring**
- **Critical Services**: Monitors Docker, Nginx, SSH, MySQL, PostgreSQL
- **System Logs**: Collects from /var/log/* files
- **Service Discovery**: Automatically discovers services and logs
- **Health Checks**: Real-time service status monitoring

## Technology Stack

### Backend
- **Python 3.10+**: Main programming language
- **FastAPI**: Web framework for API
- **Google Gemini API**: AI log analysis
- **Docker**: Containerization for Fluent Bit

### Frontend
- **HTML/CSS/JavaScript**: Dashboard UI
- **Modern CSS**: Gradients, animations, responsive design
- **Font Awesome**: Icons

### Infrastructure
- **Fluent Bit**: Log collection and processing
- **Docker Compose**: Container orchestration
- **Systemd**: Service management
- **Linux**: Operating system

## Configuration

### Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (optional, for AI analysis)
- `FLUENT_BIT_LOG_PATH`: Path to Fluent Bit log file (optional)

### Ports
- **5001**: Dashboard API server
- **8888**: Fluent Bit HTTP endpoint (optional)

## Setup Requirements

### Required
- Python 3.10+
- Docker (for Fluent Bit, optional)
- Linux system (for system log access)

### Optional
- Google Gemini API key (for AI analysis)
- Docker Compose (for Fluent Bit setup)

## Usage

### Start the System
```bash
# Start API server
cd /home/kasun/Documents/Heal-X-Bot
python3 monitoring/server/healing_dashboard_api.py

# Start Fluent Bit (optional)
./scripts/start-fluent-bit.sh
```

### Access Dashboard
- URL: http://localhost:5001
- Features: Log viewing, AI analysis, service monitoring

### Analyze Logs with AI
1. Open dashboard
2. Go to "Logs & AI" tab
3. Select log source (Fluent Bit or Centralized Logger)
4. Click "Analyze" on any log entry
5. View AI analysis in the panel

## Recent Changes Summary

### Files Modified
- `monitoring/server/gemini_log_analyzer.py` - Fixed API client
- `monitoring/server/healing_dashboard_api.py` - Enhanced Fluent Bit support
- `monitoring/dashboard/static/healing-dashboard.html` - Added AI analysis
- `config/fluent-bit/fluent-bit.conf` - Fixed configuration
- `scripts/start-fluent-bit.sh` - Enhanced startup script

### Files Added
- 9 documentation files
- 4 helper scripts
- Configuration improvements

### Statistics
- **20 files changed**
- **29,212+ lines added**
- **122 lines removed**
- **1 major commit**

## Future Improvements

### Potential Enhancements
1. **More Log Sources**: Add support for more log sources
2. **Advanced Filtering**: More sophisticated filtering options
3. **Export Features**: Export logs and analysis
4. **Notifications**: Alert system for critical errors
5. **Dashboard Themes**: Multiple UI themes
6. **Performance Metrics**: System performance monitoring
7. **Log Retention**: Configurable log retention policies

## Support

### Documentation
- See individual `.md` files for detailed documentation
- Check `scripts/` for helper scripts
- Review configuration files for setup

### Troubleshooting
- **Fluent Bit Issues**: See `FLUENT_BIT_FIX.md`
- **AI Analysis Issues**: See `AI_ANALYSIS_FLUENT_BIT.md`
- **Dashboard Issues**: See `FLUENT_BIT_DASHBOARD_FIX.md`

## Repository Information

- **GitHub**: https://github.com/KAXUN01/Heal-X-Bot
- **Latest Commit**: ecd7225 - Fix Fluent Bit logs and add AI analysis feature
- **Branch**: main
- **Status**: Ready to push (authentication required)

## Conclusion

The Heal-X-Bot repository now includes:
- ✅ Fixed Gemini AI API client
- ✅ Working Fluent Bit integration
- ✅ AI analysis for Fluent Bit logs
- ✅ Enhanced error handling
- ✅ Comprehensive documentation
- ✅ Helper scripts for troubleshooting
- ✅ Improved user experience

The system is fully functional and ready for use!
