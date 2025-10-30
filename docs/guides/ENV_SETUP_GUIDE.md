# 🔐 Environment Variables Setup Guide

## Overview

All API keys, credentials, and configuration settings for the **Automatic Self-Healing Bot** are stored in a `.env` file in the project root directory. This keeps sensitive information secure and separate from code.

---

## 📋 Quick Setup

### Step 1: Create .env File

If you don't have a `.env` file yet, create one from the template:

**Windows (PowerShell):**
```powershell
Copy-Item env.template .env
```

**Linux/Mac:**
```bash
cp env.template .env
```

### Step 2: Edit .env File

Open the `.env` file in any text editor and add your actual API keys and credentials.

---

## 🔑 Required Configuration

### **1. Google Gemini API Key** (REQUIRED for AI Log Analysis)

This is **essential** for the AI-powered log analysis feature.

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**How to Get:**
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in your `.env` file

**Note:** You can also use `GOOGLE_API_KEY` - both work.

---

## ⚙️ Optional Configuration

### **2. Slack Integration** (Optional)

For sending alerts to Slack:

```env
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**How to Get:**
1. Go to: https://api.slack.com/messaging/webhooks
2. Create a new Incoming Webhook
3. Copy the webhook URL
4. Paste it in your `.env` file

### **3. AWS S3 Configuration** (Optional)

For uploading logs to AWS S3:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name
```

**How to Get:**
1. Go to AWS IAM Console
2. Create a new user with S3 access
3. Generate access keys
4. Create an S3 bucket
5. Add credentials to `.env`

### **4. Grafana Configuration** (Optional)

For Grafana dashboard admin password:

```env
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

Default: `admin`

### **5. Port Configuration** (Optional)

Override default ports if needed:

```env
MODEL_PORT=8080
DASHBOARD_PORT=3001
NETWORK_ANALYZER_PORT=8000
INCIDENT_BOT_PORT=8000
MONITORING_SERVER_PORT=5000
```

**Defaults are fine for most cases.**

---

## 📝 Complete .env File Example

```env
# =============================================================================
# AUTOMATIC SELF-HEALING BOT - ENVIRONMENT CONFIGURATION
# =============================================================================

# -----------------------------------------------------------------------------
# AI Configuration (REQUIRED for AI Log Analysis)
# -----------------------------------------------------------------------------
# Get your free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=AIzaSyABC123def456GHI789jkl012MNO345pqr678

# Alternative (both work, GEMINI_API_KEY takes precedence)
# GOOGLE_API_KEY=AIzaSyABC123def456GHI789jkl012MNO345pqr678

# -----------------------------------------------------------------------------
# Slack Integration (OPTIONAL)
# -----------------------------------------------------------------------------
# For sending alerts and notifications to Slack
# Get webhook URL from: https://api.slack.com/messaging/webhooks
SLACK_WEBHOOK=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

# -----------------------------------------------------------------------------
# AWS S3 Configuration (OPTIONAL)
# -----------------------------------------------------------------------------
# For uploading logs and incident reports to S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=healing-bot-logs

# -----------------------------------------------------------------------------
# Grafana Configuration (OPTIONAL)
# -----------------------------------------------------------------------------
# Admin password for Grafana dashboard
GRAFANA_ADMIN_PASSWORD=secure_password_here

# -----------------------------------------------------------------------------
# Port Configuration (OPTIONAL - Defaults work for most cases)
# -----------------------------------------------------------------------------
# Override these only if you have port conflicts
MODEL_PORT=8080
DASHBOARD_PORT=3001
NETWORK_ANALYZER_PORT=8000
INCIDENT_BOT_PORT=8000
MONITORING_SERVER_PORT=5000

# -----------------------------------------------------------------------------
# Self-Healing Configuration (OPTIONAL)
# -----------------------------------------------------------------------------
# Enable/disable automatic self-healing
SELF_HEALING_ENABLED=false

# Confidence threshold for auto-healing (0.0 to 1.0)
# Higher = more conservative, only heal high-confidence issues
SELF_HEALING_CONFIDENCE_THRESHOLD=0.8
```

---

## ✅ Verification

### Check if .env is Loaded

After creating your `.env` file, verify it's being loaded:

**Test 1: Check Gemini API Key**
```bash
cd monitoring/server
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ Gemini API Key:', 'FOUND' if os.getenv('GEMINI_API_KEY') else '❌ NOT FOUND')"
```

**Test 2: Start Monitoring Server**
```bash
cd monitoring/server
python app.py
```

You should see:
- ✅ No warnings about missing GEMINI_API_KEY
- ✅ "Gemini AI log analyzer initialized"

If you see warnings, check that:
1. `.env` file exists in project root
2. `GEMINI_API_KEY` is set in `.env`
3. No typos in the variable name

---

## 🔒 Security Best Practices

### 1. Never Commit .env File

The `.env` file is in `.gitignore` - **never commit it to Git!**

```bash
# Check .gitignore contains:
.env
```

### 2. Use Different Keys for Different Environments

```env
# Development
GEMINI_API_KEY=dev_key_here

# Production (use different .env file)
GEMINI_API_KEY=prod_key_here
```

### 3. Rotate Keys Regularly

Change your API keys every 3-6 months for security.

### 4. Restrict API Key Permissions

- For Gemini: Restrict to your IP if possible
- For AWS: Use IAM roles with minimal permissions
- For Slack: Limit webhook to specific channel

---

## 🚀 Services That Use .env

### ✅ All Services Load from .env

All services now automatically load environment variables from `.env`:

1. **Monitoring Server** (`monitoring/server/app.py`)
   - Loads: `GEMINI_API_KEY`, all port configs

2. **Dashboard** (`monitoring/dashboard/app.py`)
   - Loads: Port configs, model URLs

3. **Incident Bot** (`incident-bot/main.py`)
   - Loads: `GEMINI_API_KEY`, `SLACK_WEBHOOK`, AWS credentials

4. **Model API** (`model/main.py`)
   - Loads: Port configs

5. **Network Analyzer** (`monitoring/server/network_analyzer.py`)
   - Loads: Port configs

---

## 🔧 Troubleshooting

### Problem: "GEMINI_API_KEY not found"

**Solution:**
1. Check `.env` file exists in project root
2. Check spelling: `GEMINI_API_KEY` (not `GEMENI` or `GEMINI_KEY`)
3. Check no spaces around `=`: `GEMINI_API_KEY=key` (not `GEMINI_API_KEY = key`)
4. Restart the server after editing `.env`

### Problem: "python-dotenv not found"

**Solution:**
```bash
pip install python-dotenv
```

Or reinstall requirements:
```bash
pip install -r requirements.txt
```

### Problem: AI Analysis says "API key not configured"

**Solution:**
1. Verify `.env` has `GEMINI_API_KEY`
2. Check the key is valid (try at https://makersuite.google.com/)
3. Restart monitoring server
4. Check logs for errors

### Problem: Port conflicts

**Solution:**
Change ports in `.env`:
```env
DASHBOARD_PORT=3002  # Changed from 3001
MODEL_PORT=8081      # Changed from 8080
```

---

## 📊 Environment Variable Reference

| Variable | Required? | Used By | Purpose |
|----------|-----------|---------|---------|
| `GEMINI_API_KEY` | **YES** for AI | Monitoring Server, Incident Bot | AI log analysis |
| `GOOGLE_API_KEY` | Alternative | Same as above | Alternative to GEMINI_API_KEY |
| `SLACK_WEBHOOK` | NO | Incident Bot | Send alerts to Slack |
| `AWS_ACCESS_KEY_ID` | NO | Incident Bot | Upload to S3 |
| `AWS_SECRET_ACCESS_KEY` | NO | Incident Bot | Upload to S3 |
| `AWS_REGION` | NO | Incident Bot | S3 region |
| `S3_BUCKET_NAME` | NO | Incident Bot | S3 bucket name |
| `GRAFANA_ADMIN_PASSWORD` | NO | Grafana | Dashboard password |
| `MODEL_PORT` | NO | Model API | API port |
| `DASHBOARD_PORT` | NO | Dashboard | Dashboard port |
| `NETWORK_ANALYZER_PORT` | NO | Network Analyzer | Analyzer port |
| `INCIDENT_BOT_PORT` | NO | Incident Bot | Bot port |
| `SELF_HEALING_ENABLED` | NO | Incident Bot | Enable auto-healing |
| `SELF_HEALING_CONFIDENCE_THRESHOLD` | NO | Incident Bot | Healing threshold |

---

## 🎯 Quick Reference

### Minimal Setup (AI Analysis Only)
```env
GEMINI_API_KEY=your_key_here
```

### Full Setup (All Features)
```env
GEMINI_API_KEY=your_gemini_key
SLACK_WEBHOOK=your_slack_webhook
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket
```

---

## 📞 Need Help?

- **Gemini API Issues**: https://ai.google.dev/docs
- **Slack Webhooks**: https://api.slack.com/messaging/webhooks
- **AWS S3**: https://docs.aws.amazon.com/s3/

---

**🔐 Keep your .env file secure and never share it publicly!**

