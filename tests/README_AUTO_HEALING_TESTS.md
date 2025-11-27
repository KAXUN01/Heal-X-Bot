# Auto-Healing Dashboard Test Suite

This directory contains comprehensive test scripts for the Autonomous Self-Healing & Cloud Simulation dashboard.

## Test Files

### 1. `test_auto_healing_api.py`
**Backend API Tests** - Tests all auto-healing related API endpoints

**Coverage:**
- `/api/cloud/healing/history` - Healing history retrieval
- `/api/auto-healer/status` - Auto-healer status and configuration
- `/api/auto-healer/config` - Configuration updates
- `/api/cloud/faults` - Active faults detection
- `/api/cloud/faults/{fault_id}/heal` - Manual fault healing
- `/api/cloud/faults/inject` - Fault injection for testing

**Test Cases:**
- Successful API calls
- Error handling (service unavailable, not initialized)
- Empty data responses
- Invalid input validation
- Partial configuration updates

**Run:**
```bash
pytest tests/test_auto_healing_api.py -v
```

### 2. `test_auto_healing_frontend.py`
**Frontend Functionality Tests** - Tests DOM elements and JavaScript functions

**Coverage:**
- DOM element existence (status cards, statistics, forms, etc.)
- JavaScript function availability
- Chart.js initialization
- Form interactions
- Error message display
- Loading states

**Requirements:**
- Selenium WebDriver
- Chrome browser (or ChromeDriver)

**Run:**
```bash
pytest tests/test_auto_healing_frontend.py -v -s
```

### 3. `test_auto_healing_e2e.py`
**End-to-End Integration Tests** - Tests complete user workflows

**Coverage:**
- Complete dashboard viewing workflow
- Configuration update workflow
- Real-time data updates
- Error scenario handling
- API integration from frontend
- Complete user journey

**Requirements:**
- Selenium WebDriver
- Chrome browser (or ChromeDriver)
- Backend server running on `http://localhost:8000`

**Run:**
```bash
pytest tests/test_auto_healing_e2e.py -v -s
```

## Setup

### Install Dependencies

```bash
pip install pytest pytest-asyncio fastapi[all] selenium requests
```

### Install ChromeDriver

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Or download from https://chromedriver.chromium.org/
```

**macOS:**
```bash
brew install chromedriver
```

**Windows:**
Download from https://chromedriver.chromium.org/ and add to PATH

### Start Backend Server

Before running frontend or E2E tests, ensure the backend server is running:

```bash
cd monitoring/server
python -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 8000
```

## Running Tests

### Run All Tests
```bash
pytest tests/test_auto_healing_*.py -v
```

### Run Specific Test File
```bash
pytest tests/test_auto_healing_api.py -v
pytest tests/test_auto_healing_frontend.py -v -s
pytest tests/test_auto_healing_e2e.py -v -s
```

### Run Specific Test Class
```bash
pytest tests/test_auto_healing_api.py::TestHealingHistoryAPI -v
```

### Run Specific Test
```bash
pytest tests/test_auto_healing_api.py::TestHealingHistoryAPI::test_get_healing_history_success -v
```

### Run with Coverage
```bash
pytest tests/test_auto_healing_*.py --cov=monitoring.server.healing_dashboard_api --cov-report=html
```

## Test Configuration

### Environment Variables

You can configure test settings via environment variables:

- `BASE_URL` - Frontend URL (default: `http://localhost:8000`)
- `API_BASE_URL` - Backend API URL (default: `http://localhost:8000`)
- `TIMEOUT` - Test timeout in seconds (default: 10-15)

### Headless Mode

Frontend and E2E tests run in headless mode by default. To see the browser:

Edit the test files and remove or comment out:
```python
chrome_options.add_argument("--headless")
```

## Troubleshooting

### Tests Fail with "WebDriver not available"
- Ensure ChromeDriver is installed and in PATH
- Check ChromeDriver version matches Chrome browser version
- Try running with `--headless` flag removed to see browser

### Tests Fail with "Connection refused"
- Ensure backend server is running on port 8000
- Check firewall settings
- Verify BASE_URL and API_BASE_URL are correct

### Tests Fail with "Element not found"
- Increase TIMEOUT value in test files
- Check if page has fully loaded
- Verify element IDs match the HTML

### API Tests Fail with "Auto-healer not initialized"
- This is expected if auto-healer service is not running
- Tests should handle this gracefully and verify error responses
- To test with real service, ensure auto-healer is initialized in backend

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run API Tests
  run: pytest tests/test_auto_healing_api.py -v

- name: Run Frontend Tests
  run: |
    sudo apt-get install -y chromium-chromedriver
    pytest tests/test_auto_healing_frontend.py -v

- name: Run E2E Tests
  run: |
    # Start server in background
    python -m uvicorn monitoring.server.healing_dashboard_api:app --host 0.0.0.0 --port 8000 &
    sleep 5
    pytest tests/test_auto_healing_e2e.py -v
```

## Test Maintenance

### Adding New Tests

1. **API Tests**: Add new test methods to appropriate test class in `test_auto_healing_api.py`
2. **Frontend Tests**: Add new test methods to appropriate test class in `test_auto_healing_frontend.py`
3. **E2E Tests**: Add new workflow tests to `test_auto_healing_e2e.py`

### Updating Tests

When UI or API changes:
1. Update test selectors (IDs, XPath, etc.)
2. Update expected responses
3. Add tests for new features
4. Remove tests for deprecated features

## Notes

- Frontend and E2E tests require a running backend server
- Some tests may be skipped if services are not available (this is expected)
- Tests use mocks where possible to avoid dependencies on external services
- Real browser tests are slower but provide better coverage

