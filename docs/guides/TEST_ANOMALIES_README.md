# 🧪 Anomalies Feature Test Script

## Overview

`test_anomalies_feature.py` is a comprehensive test script that validates the "Detected Anomalies & Errors" feature in the Healing-bot dashboard.

---

## What It Tests

### ✅ Test 1: Server Connectivity
- Verifies monitoring server is running on port 5000
- Checks health endpoint

### ✅ Test 2: Critical Services Issues Endpoint
- Tests `/api/critical-services/issues`
- Validates response format
- Shows count and sample issues

### ✅ Test 3: System Logs Endpoint (Fallback)
- Tests `/api/system-logs/recent?level=ERROR`
- Verifies fallback mechanism works
- Shows ERROR level logs

### ✅ Test 4: AI Analysis Integration
- Posts sample log to `/api/gemini/analyze-log`
- Verifies AI analysis works
- Displays analysis sections (What Happened, Quick Fix, Prevention)

### ✅ Test 5: Dashboard Availability
- Checks if dashboard is accessible on port 3001
- Provides manual testing instructions

---

## Prerequisites

### 1. Services Running

Make sure these services are running:

```bash
# Terminal 1: Monitoring Server
cd monitoring/server
source ../../venv/bin/activate
python app.py

# Terminal 2: Dashboard
cd monitoring/dashboard
source ../../venv/bin/activate
python app.py
```

### 2. Python Dependencies

The script auto-installs these if needed:
- `requests` - HTTP library
- `colorama` - Colored terminal output

---

## Usage

### Run the Test Script

```bash
# Make executable (first time only)
chmod +x test_anomalies_feature.py

# Run tests
python test_anomalies_feature.py

# Or with virtual environment
source venv/bin/activate
python test_anomalies_feature.py
```

### Expected Output

```
╔══════════════════════════════════════════════════════════════════════╗
║        🧪 ANOMALIES & ERRORS FEATURE - TEST SUITE 🧪                ║
╚══════════════════════════════════════════════════════════════════════╝

======================================================================
                     TEST 1: Server Connectivity                      
======================================================================
✅ Monitoring server is running on http://localhost:5000

======================================================================
              TEST 2: Critical Services Issues Endpoint               
======================================================================
✅ Endpoint is responding correctly
✅ No critical issues found - system is healthy!

[... more tests ...]

======================================================================
                             TEST SUMMARY                             
======================================================================
Total Tests:   5
Passed:        5
Failed:        0
Success Rate:  100.0%

                        🎉 ALL TESTS PASSED! 🎉                         
```

---

## Test Scenarios

### Scenario 1: All Tests Pass (100%)
✅ All services running  
✅ API endpoints working  
✅ AI analysis functional  
✅ Dashboard accessible  

**Action:** Feature is ready to use!

### Scenario 2: Monitoring Server Down
❌ Test 1 fails  
⚠️  Remaining tests skipped  

**Action:** Start monitoring server:
```bash
cd monitoring/server && python app.py
```

### Scenario 3: Dashboard Down
✅ Tests 1-4 pass  
❌ Test 5 fails  

**Action:** Start dashboard:
```bash
cd monitoring/dashboard && python app.py
```

### Scenario 4: AI Analysis Fails
✅ Tests 1-3, 5 pass  
❌ Test 4 fails (API key issue)  

**Action:** Configure Gemini API key:
1. Get free key: https://aistudio.google.com/app/apikey
2. Add to `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Restart monitoring server

---

## Output Details

### Color Coding

- 🟢 **Green (✅)** - Test passed successfully
- 🔴 **Red (❌)** - Test failed
- 🟡 **Yellow (⚠️)** - Warning or partial success
- 🔵 **Blue (ℹ️)** - Information message

### Test Results

Each test shows:
1. **Endpoint URL** - What's being tested
2. **Response Data** - JSON response (formatted)
3. **Status** - Pass/Fail with details
4. **Recommendations** - What to do if failed

---

## Manual Testing Steps

After running the script, manually verify in browser:

### Step 1: Open Dashboard
```
http://localhost:3001
```

### Step 2: Navigate to Logs Tab
Click **"Logs & AI Analysis"** in the top navigation

### Step 3: Check Anomalies Section
Scroll down to **"Detected Anomalies & Errors"** table

### Step 4: Verify Display

**If Healthy:**
```
┌──────────────────────────────────────────────────────┐
│ ✅ No critical anomalies detected - System running   │
│    smoothly!                                         │
└──────────────────────────────────────────────────────┘
```

**If Issues Found:**
```
┌────────────────────────────────────────────────────────┐
│ Time      | Service  | Severity | Message  | Actions  │
├────────────────────────────────────────────────────────┤
│ 2:30 PM   | docker   | ERROR    | Failed.. | [Analyze]│
└────────────────────────────────────────────────────────┘
```

### Step 5: Test AI Analysis
1. Click **"Analyze"** button on any anomaly
2. Verify AI analysis panel shows:
   - 🔍 What Happened
   - 💡 Quick Fix
   - 🛡️ Prevention
3. Check for modern gradient styling

---

## Troubleshooting

### Issue: "Cannot connect to monitoring server"

**Solution:**
```bash
# Check if server is running
lsof -i:5000

# If not, start it
cd monitoring/server
python app.py
```

### Issue: "Cannot connect to dashboard"

**Solution:**
```bash
# Check if dashboard is running
lsof -i:3001

# If not, start it
cd monitoring/dashboard
python app.py
```

### Issue: "AI analysis failed - API key"

**Solution:**
1. Get API key: https://aistudio.google.com/app/apikey
2. Edit `.env` file:
   ```bash
   GEMINI_API_KEY=AIza...your_key_here
   ```
3. Restart services

### Issue: "No critical issues found"

**Solution:**
This is actually good! It means your system is healthy.

To test with sample data:
1. The script creates a test log automatically
2. Check if AI analysis (Test 4) still works
3. Feature will show real issues when they occur

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All tests passed |
| 1 | One or more tests failed |
| 130 | Interrupted by user (Ctrl+C) |

---

## Integration with CI/CD

You can use this script in automated testing:

```bash
#!/bin/bash
# ci-test.sh

# Start services
./start-healing-bot.sh &
sleep 10

# Run tests
python test_anomalies_feature.py
EXIT_CODE=$?

# Cleanup
pkill -f "python.*app.py"

exit $EXIT_CODE
```

---

## Script Structure

```python
test_anomalies_feature.py
├── Configuration
│   ├── MONITORING_SERVER (port 5000)
│   └── DASHBOARD_URL (port 3001)
├── Helper Functions
│   ├── print_header()
│   ├── print_success()
│   ├── print_error()
│   ├── print_info()
│   └── print_warning()
├── Test Functions
│   ├── test_server_connectivity()
│   ├── test_critical_services_endpoint()
│   ├── test_system_logs_endpoint()
│   ├── test_ai_analysis()
│   └── test_dashboard_availability()
└── Main Functions
    ├── run_all_tests()
    └── print_summary()
```

---

## Example Test Run

```bash
$ python test_anomalies_feature.py

🧪 Running Tests...

TEST 1: Server Connectivity
✅ Monitoring server is running

TEST 2: Critical Services Issues
✅ Endpoint responding
✅ Found 3 issues

TEST 3: System Logs Endpoint
✅ Fallback working
✅ Found 5 ERROR logs

TEST 4: AI Analysis
✅ AI analysis successful
📊 What Happened: [AI explanation]
💡 Quick Fix: [Steps]
🛡️ Prevention: [Tips]

TEST 5: Dashboard
✅ Dashboard accessible

SUMMARY: 5/5 tests passed (100%)
🎉 ALL TESTS PASSED!
```

---

## Contributing

To add more tests:

1. Create new test function:
   ```python
   def test_new_feature():
       print_header("TEST 6: New Feature")
       # Your test logic here
       return True  # or False
   ```

2. Add to `run_all_tests()`:
   ```python
   results['total'] += 1
   if test_new_feature():
       results['passed'] += 1
   else:
       results['failed'] += 1
   ```

---

## Related Documentation

- **ANOMALIES_SECTION_FIX.md** - Detailed fix documentation
- **AI_ANALYSIS_MODERNIZATION.md** - AI feature documentation
- **CRITICAL_SERVICES_GUIDE.md** - Critical services monitoring

---

**Created:** October 29, 2025  
**Version:** 1.0  
**Status:** ✅ Production Ready

