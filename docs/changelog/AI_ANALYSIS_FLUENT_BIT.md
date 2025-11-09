# AI Analysis for Fluent Bit Logs

## Feature Added
AI analysis is now fully integrated with Fluent Bit logs! You can analyze any Fluent Bit log entry using Google Gemini AI, just like centralized logs.

## How to Use

### 1. Analyze Individual Log Entries
1. Open the dashboard: `http://localhost:5001`
2. Navigate to "Logs & AI" tab
3. Select "Fluent Bit" as log source
4. Find any log entry in the table
5. Click the **"Analyze"** button on any log row
6. AI analysis will appear in the AI Analysis Panel below

### 2. Quick Analyze Recent Errors
1. In the "Logs & AI" tab
2. Click the **"Quick Analyze Errors"** button in the AI Analysis Panel
3. This analyzes recent errors/warnings from Fluent Bit logs
4. Provides pattern analysis and recommendations

## Features

### Individual Log Analysis
- **What Happened**: Root cause analysis
- **Quick Fix**: Immediate actionable steps
- **Prevention**: Long-term recommendations
- **Severity Assessment**: Automatic severity detection

### Pattern Analysis
- **Common Issues**: Most frequent errors
- **Timeline**: How issues evolved
- **Correlation**: Related errors
- **Recommendations**: Prioritized fixes

## What's Enhanced

### 1. Log Format Compatibility
- Fluent Bit logs are automatically formatted for AI analysis
- All required fields (timestamp, service, message, level) are included
- Works seamlessly with existing AI analysis API

### 2. Visual Indicators
- AI Analysis Panel shows log source (Fluent Bit vs Centralized Logger)
- Clear indication when analyzing Fluent Bit logs
- Status messages during analysis

### 3. Quick Analyze
- Quick Analyze now works with both Fluent Bit and Centralized Logger
- Automatically detects which log source is active
- Analyzes errors from the selected source

## API Endpoints

### Analyze Single Log
```bash
POST /api/gemini/analyze-log
Content-Type: application/json

{
  "timestamp": "2025-11-08T16:00:00",
  "service": "syslog",
  "message": "ERROR: Connection failed",
  "level": "ERROR",
  "source_file": "syslog",
  "source": "fluent-bit",
  "tag": "syslog"
}
```

### Quick Analyze Errors
```bash
GET /api/gemini/quick-analyze
```
- Automatically uses Fluent Bit logs if available
- Falls back to Centralized Logger if Fluent Bit has no errors
- Returns pattern analysis of recent errors

## Requirements

### Gemini API Key
To use AI analysis, you need a Gemini API key:

1. Get API key: https://aistudio.google.com/app/apikey
2. Add to `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
3. Restart the API server

### Without API Key
- Logs will still display
- AI analysis will show a helpful error message
- System works perfectly without AI (AI is optional)

## Example Analysis

### Input (Fluent Bit Log)
```
Service: syslog
Level: ERROR
Message: kernel: [12345.678] Out of memory: Kill process 1234 (python) score 500
Timestamp: 2025-11-08T16:00:00
```

### AI Analysis Output
```
🔍 WHAT HAPPENED:
The system ran out of memory and the kernel's OOM (Out of Memory) killer 
terminated a Python process. This typically occurs when available RAM is 
exhausted and the system cannot allocate more memory.

💡 QUICK FIX:
1. Check current memory usage: free -h
2. Identify memory-consuming processes: ps aux --sort=-%mem | head
3. Kill or restart memory-intensive processes if needed
4. Consider adding swap space: sudo fallocate -l 2G /swapfile

🛡️ PREVENTION:
- Monitor memory usage regularly
- Set memory limits for applications
- Add swap space if physical RAM is limited
- Optimize applications to use less memory
```

## Troubleshooting

### AI Analysis Not Working
1. Check if Gemini API key is configured: `grep GEMINI_API_KEY .env`
2. Check API server logs: `tail -f /tmp/healing-dashboard.log | grep -i gemini`
3. Verify API key is valid: Visit https://aistudio.google.com/app/apikey

### No Logs Available
1. Ensure Fluent Bit is running: `docker ps | grep fluent-bit`
2. Check Fluent Bit logs: `docker logs fluent-bit`
3. Verify log file exists: `ls -lh logs/fluent-bit/fluent-bit-output.jsonl`

### Analysis Takes Too Long
- Gemini API calls may take 2-5 seconds
- Large log messages may take longer
- Check your internet connection
- Verify API key rate limits

## Summary

✅ **AI Analysis works with Fluent Bit logs**
✅ **Individual log analysis available**
✅ **Quick analyze errors feature**
✅ **Pattern analysis and recommendations**
✅ **Works with or without API key (optional feature)**

The AI analysis feature is now fully integrated with Fluent Bit logs. Simply click "Analyze" on any log entry to get intelligent insights!
