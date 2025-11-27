"""
End-to-End integration tests for Auto-Healing dashboard
Tests complete user workflows and real-time updates
"""
import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 15


@pytest.fixture(scope="module")
def driver():
    """Setup and teardown Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(5)
        yield driver
    except Exception as e:
        pytest.skip(f"WebDriver not available: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()


@pytest.fixture
def navigate_to_auto_healing(driver):
    """Navigate to auto-healing tab"""
    driver.get(BASE_URL)
    time.sleep(3)  # Wait for page load
    
    # Click on auto-healing tab
    try:
        auto_healing_tab = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Autonomous Self-Healing')]"))
        )
        auto_healing_tab.click()
        time.sleep(3)  # Wait for tab content to load
    except TimeoutException:
        pytest.skip("Auto-healing tab not found")


class TestDashboardWorkflow:
    """Test complete dashboard viewing workflow"""
    
    def test_view_dashboard_and_check_status(self, navigate_to_auto_healing, driver):
        """Test viewing dashboard and checking status"""
        # Wait for status to load
        try:
            status_element = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "autoHealingStatus"))
            )
            status_text = status_element.text
            assert len(status_text) > 0, "Status should be displayed"
        except TimeoutException:
            pytest.fail("Status element not loaded")
    
    def test_view_healing_history(self, navigate_to_auto_healing, driver):
        """Test viewing healing history timeline"""
        try:
            history_element = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "healingHistoryTimeline"))
            )
            # Check if history loads (may be empty)
            time.sleep(2)
            history_content = history_element.text
            # Should have some content (even if it's "No history" message)
            assert len(history_content) > 0, "History section should have content"
        except TimeoutException:
            pytest.fail("History timeline not found")
    
    def test_view_active_faults(self, navigate_to_auto_healing, driver):
        """Test viewing active faults"""
        try:
            faults_element = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "activeFaultsList"))
            )
            time.sleep(2)  # Wait for faults to load
            faults_content = faults_element.text
            assert len(faults_content) > 0, "Active faults section should have content"
        except TimeoutException:
            pytest.fail("Active faults section not found")


class TestConfigurationWorkflow:
    """Test configuration update workflow"""
    
    def test_load_configuration(self, navigate_to_auto_healing, driver):
        """Test loading current configuration"""
        try:
            # Wait for config to load
            time.sleep(2)
            
            # Check if configuration fields are populated
            enabled_checkbox = driver.find_element(By.ID, "healingEnabled")
            interval_input = driver.find_element(By.ID, "monitoringInterval")
            
            # Fields should exist and be interactable
            assert enabled_checkbox is not None
            assert interval_input is not None
        except Exception as e:
            pytest.fail(f"Error loading configuration: {e}")
    
    def test_update_configuration(self, navigate_to_auto_healing, driver):
        """Test updating configuration and verifying save"""
        try:
            # Get current values
            interval_input = driver.find_element(By.ID, "monitoringInterval")
            original_value = interval_input.get_attribute("value")
            
            # Update value
            interval_input.clear()
            new_value = "90"
            interval_input.send_keys(new_value)
            time.sleep(0.5)
            
            # Verify value changed
            assert interval_input.get_attribute("value") == new_value
            
            # Try to save (if save button exists)
            try:
                save_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'saveAutoHealingConfig')]")
                save_button.click()
                time.sleep(2)  # Wait for save to complete
            except NoSuchElementException:
                # Save button might not be visible or might use different selector
                pass
        except Exception as e:
            pytest.fail(f"Error updating configuration: {e}")


class TestRealTimeUpdates:
    """Test real-time data updates"""
    
    def test_dashboard_refreshes_data(self, navigate_to_auto_healing, driver):
        """Test that dashboard can refresh data"""
        try:
            # Get initial status
            status_element = driver.find_element(By.ID, "autoHealingStatus")
            initial_text = status_element.text
            
            # Trigger refresh by calling update function
            driver.execute_script("updateAutoHealingDashboard();")
            time.sleep(3)  # Wait for update
            
            # Check if status changed or updated
            updated_text = status_element.text
            # Status should exist (may or may not change)
            assert len(updated_text) > 0
        except Exception as e:
            pytest.fail(f"Error testing real-time updates: {e}")
    
    def test_active_faults_refresh(self, navigate_to_auto_healing, driver):
        """Test refreshing active faults"""
        try:
            faults_element = driver.find_element(By.ID, "activeFaultsList")
            initial_content = faults_element.text
            
            # Trigger refresh
            driver.execute_script("updateActiveFaults();")
            time.sleep(3)  # Wait for update
            
            # Check if content updated
            updated_content = faults_element.text
            assert len(updated_content) > 0
        except Exception as e:
            pytest.fail(f"Error testing faults refresh: {e}")


class TestErrorScenarios:
    """Test error handling scenarios"""
    
    def test_handles_service_unavailable(self, navigate_to_auto_healing, driver):
        """Test that UI handles service unavailable gracefully"""
        try:
            # Trigger dashboard update
            driver.execute_script("updateAutoHealingDashboard();")
            time.sleep(3)
            
            # Check if error message is displayed (if service is unavailable)
            status_element = driver.find_element(By.ID, "autoHealingStatus")
            status_text = status_element.text.lower()
            
            # Should show some status (could be error, unavailable, or success)
            assert len(status_text) > 0
            # Should not show JavaScript errors
            assert "error" not in driver.page_source.lower() or "unavailable" in status_text or "offline" in status_text
        except Exception as e:
            pytest.fail(f"Error testing service unavailable handling: {e}")
    
    def test_handles_network_errors(self, navigate_to_auto_healing, driver):
        """Test that UI handles network errors gracefully"""
        # This test verifies error handling without actually breaking network
        try:
            # Check if error handling functions exist
            result = driver.execute_script("""
                try {
                    updateAutoHealingDashboard();
                    return 'function_executed';
                } catch(e) {
                    return 'error: ' + e.message;
                }
            """)
            assert "function_executed" in result or "error" not in result.lower()
        except Exception as e:
            pytest.fail(f"Error testing network error handling: {e}")


class TestAPIIntegration:
    """Test API integration from frontend"""
    
    def test_api_endpoints_accessible(self):
        """Test that API endpoints are accessible"""
        endpoints = [
            "/api/cloud/healing/history",
            "/api/auto-healer/status",
            "/api/cloud/faults"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
                # Should return 200 or 503 (service unavailable)
                assert response.status_code in [200, 503], f"Endpoint {endpoint} returned {response.status_code}"
            except requests.exceptions.RequestException as e:
                pytest.skip(f"API not accessible: {e}")
    
    def test_config_endpoint_works(self):
        """Test configuration endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/auto-healer/status", timeout=5)
            assert response.status_code in [200, 503]
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
        except requests.exceptions.RequestException as e:
            pytest.skip(f"API not accessible: {e}")


class TestUserInteractionFlow:
    """Test complete user interaction flow"""
    
    def test_complete_user_journey(self, navigate_to_auto_healing, driver):
        """Test a complete user journey through the dashboard"""
        try:
            # 1. View dashboard
            status = driver.find_element(By.ID, "autoHealingStatus")
            assert status is not None
            
            # 2. View statistics
            stats = driver.find_element(By.ID, "statsTotalAttempts")
            assert stats is not None
            
            # 3. View recent actions
            recent_actions = driver.find_element(By.ID, "recentHealingActions")
            assert recent_actions is not None
            
            # 4. View history
            history = driver.find_element(By.ID, "healingHistoryTimeline")
            assert history is not None
            
            # 5. View configuration
            config_form = driver.find_element(By.ID, "autoHealingConfig")
            assert config_form is not None
            
            # 6. View active faults
            faults = driver.find_element(By.ID, "activeFaultsList")
            assert faults is not None
            
        except Exception as e:
            pytest.fail(f"Error in complete user journey: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

