# 🧪 Healing-Bot Test Suite

This directory contains all testing infrastructure for the Healing-Bot system.

---

## 📁 Directory Structure

```
tests/
├── README.md (this file)
├── unit/                        # Unit tests
├── integration/                 # Integration tests
└── scripts/                     # Test scripts and utilities
```

---

## 🗂️ Test Categories

### 📜 Test Scripts (`scripts/`)

Standalone test scripts for various components:

| Script | Purpose | Usage |
|--------|---------|-------|
| **test_anomalies_feature.py** | Tests anomaly detection end-to-end | `python scripts/test_anomalies_feature.py` |
| **test-gemini.py** | Tests Gemini AI integration | `python scripts/test-gemini.py` |
| **test_gemini_models.py** | Tests available Gemini models | `python scripts/test_gemini_models.py` |
| **test-prometheus-metrics.py** | Tests Prometheus metrics | `python scripts/test-prometheus-metrics.py` |
| **validate-prometheus-config.py** | Validates Prometheus configuration | `python scripts/validate-prometheus-config.py` |
| **start_dashboard_test.py** | Dashboard startup test | `python scripts/start_dashboard_test.py` |

### 🧩 Unit Tests (`unit/`)

Component-level tests (to be added):

- Model tests
- Service tests
- Utility function tests
- Data validation tests

### 🔗 Integration Tests (`integration/`)

End-to-end and integration tests (to be added):

- API endpoint tests
- Service communication tests
- Database integration tests
- Full workflow tests

---

## 🚀 Running Tests

### Quick Test - Anomalies Feature

```bash
# Comprehensive 5-test suite for anomalies detection
cd tests/scripts
python test_anomalies_feature.py
```

**Tests:**
1. Server connectivity (port 5000)
2. Critical services issues endpoint
3. System logs fallback endpoint
4. AI analysis integration
5. Dashboard availability (port 3001)

### AI Integration Tests

```bash
# Test Gemini API connection
python scripts/test-gemini.py

# Test available Gemini models
python scripts/test_gemini_models.py
```

### Monitoring Tests

```bash
# Test Prometheus metrics
python scripts/test-prometheus-metrics.py

# Validate Prometheus configuration
python scripts/validate-prometheus-config.py
```

---

## 📊 Test Coverage

### Current Coverage

| Component | Test Scripts | Status |
|-----------|-------------|--------|
| **Anomaly Detection** | test_anomalies_feature.py | ✅ Complete |
| **AI Integration** | test-gemini.py, test_gemini_models.py | ✅ Complete |
| **Prometheus** | test-prometheus-metrics.py | ✅ Complete |
| **Dashboard** | start_dashboard_test.py | ✅ Complete |

### Planned Coverage

| Component | Status |
|-----------|--------|
| **Unit Tests** | 🚧 Planned |
| **Integration Tests** | 🚧 Planned |
| **E2E Tests** | 🚧 Planned |
| **Performance Tests** | 🚧 Planned |

---

## 🎯 Test Requirements

### Prerequisites

```bash
# Activate virtual environment
source ../venv/bin/activate

# Install test dependencies
pip install pytest requests colorama
```

### Services Required

Most tests require these services running:

- ✅ Monitoring Server (port 5000)
- ✅ Dashboard (port 3001)
- ✅ Prometheus (port 9090) - for metric tests
- ✅ Grafana (port 3000) - for dashboard tests

---

## 📝 Writing New Tests

### Test Script Template

```python
#!/usr/bin/env python3
"""
Test Script for [Feature Name]

This script tests:
1. [Test case 1]
2. [Test case 2]
3. [Test case 3]
"""

import requests
import sys
from colorama import init, Fore, Style

init(autoreset=True)

def test_feature():
    """Test feature functionality"""
    try:
        # Test logic here
        print(f"{Fore.GREEN}✅ Test passed{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Test failed: {e}{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    success = test_feature()
    sys.exit(0 if success else 1)
```

### Best Practices

1. **Use colored output** for better readability
2. **Return proper exit codes** (0 = success, 1 = failure)
3. **Include detailed error messages**
4. **Test both success and failure cases**
5. **Add documentation header**
6. **Make tests independent** (no interdependencies)

---

## 🔍 Test Output

### Successful Test Run

```
╔══════════════════════════════════════════════════════════════════════╗
║        🧪 ANOMALIES & ERRORS FEATURE - TEST SUITE 🧪                ║
╚══════════════════════════════════════════════════════════════════════╝

TEST 1: Server Connectivity
✅ Monitoring server is running

TEST 2: Critical Services Issues
✅ Endpoint is responding correctly

[... more tests ...]

SUMMARY:
Total Tests:   5
Passed:        5
Failed:        0
Success Rate:  100.0%

🎉 ALL TESTS PASSED! 🎉
```

### Failed Test Run

```
TEST 1: Server Connectivity
❌ Cannot connect to monitoring server at http://localhost:5000
ℹ️  Please ensure the monitoring server is running:
ℹ️    cd monitoring/server && python app.py

SUMMARY:
Total Tests:   5
Passed:        0
Failed:        5
Success Rate:  0.0%

❌ MULTIPLE TESTS FAILED ❌
```

---

## 🚦 CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python tests/scripts/test_anomalies_feature.py
```

---

## 📈 Test Reports

Test results are logged with:
- **Colored output** for readability
- **Detailed error messages** for debugging
- **Summary statistics** (passed/failed/total)
- **Exit codes** for automation

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: "Cannot connect to server"**
```bash
# Check if services are running
lsof -i:5000  # Monitoring server
lsof -i:3001  # Dashboard

# Start services if not running
cd monitoring/server && python app.py &
cd monitoring/dashboard && python app.py &
```

**Issue: "Module not found"**
```bash
# Activate virtual environment
source ../venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Issue: "AI analysis failed"**
```bash
# Check Gemini API key
echo $GEMINI_API_KEY

# Update .env file
GEMINI_API_KEY=your_key_here
```

---

## 📚 Related Documentation

- **Test Guide** - `../docs/guides/TEST_ANOMALIES_README.md`
- **Development Guide** - `../docs/development/` (planned)
- **API Documentation** - `../docs/api/` (planned)

---

## 🤝 Contributing

When adding new tests:

1. Place scripts in `scripts/`
2. Use descriptive filenames (`test_<feature>.py`)
3. Include documentation header
4. Follow the test template
5. Add entry to this README
6. Update test coverage table

---

**Last Updated:** October 30, 2025  
**Test Scripts:** 6  
**Coverage:** Anomalies, AI, Prometheus, Dashboard

