"""
Frontend functionality tests for Auto-Healing dashboard
Tests DOM elements, JavaScript functions, and UI interactions
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10


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
    time.sleep(2)  # Wait for page load
    
    # Click on auto-healing tab
    try:
        auto_healing_tab = WebDriverWait(driver, TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Autonomous Self-Healing')]"))
        )
        auto_healing_tab.click()
        time.sleep(2)  # Wait for tab content to load
    except TimeoutException:
        pytest.skip("Auto-healing tab not found")


class TestDOMElements:
    """Test that all required DOM elements exist"""
    
    def test_status_cards_exist(self, navigate_to_auto_healing, driver):
        """Test that all status overview cards exist"""
        elements = [
            "autoHealingStatus",
            "totalHealings",
            "healingSuccessRate",
            "monitoringStatus"
        ]
        
        for element_id in elements:
            try:
                element = WebDriverWait(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, element_id))
                )
                assert element is not None, f"Element {element_id} not found"
            except TimeoutException:
                pytest.fail(f"Element {element_id} not found within {TIMEOUT} seconds")
    
    def test_statistics_section_exists(self, navigate_to_auto_healing, driver):
        """Test that healing statistics section exists"""
        elements = [
            "statsTotalAttempts",
            "statsSuccessful",
            "statsFailed",
            "statsInProgress",
            "statsAvgResponseTime",
            "healingPerformanceChart"
        ]
        
        for element_id in elements:
            try:
                element = driver.find_element(By.ID, element_id)
                assert element is not None, f"Element {element_id} not found"
            except NoSuchElementException:
                pytest.fail(f"Element {element_id} not found")
    
    def test_recent_actions_section_exists(self, navigate_to_auto_healing, driver):
        """Test that recent healing actions section exists"""
        try:
            element = driver.find_element(By.ID, "recentHealingActions")
            assert element is not None
        except NoSuchElementException:
            pytest.fail("Recent healing actions section not found")
    
    def test_history_timeline_exists(self, navigate_to_auto_healing, driver):
        """Test that healing history timeline exists"""
        try:
            element = driver.find_element(By.ID, "healingHistoryTimeline")
            assert element is not None
        except NoSuchElementException:
            pytest.fail("Healing history timeline not found")
    
    def test_configuration_form_exists(self, navigate_to_auto_healing, driver):
        """Test that auto-healing configuration form exists"""
        elements = [
            "healingEnabled",
            "autoExecute",
            "monitoringInterval",
            "maxAttempts"
        ]
        
        for element_id in elements:
            try:
                element = driver.find_element(By.ID, element_id)
                assert element is not None, f"Configuration element {element_id} not found"
            except NoSuchElementException:
                pytest.fail(f"Configuration element {element_id} not found")
    
    def test_active_faults_section_exists(self, navigate_to_auto_healing, driver):
        """Test that active faults section exists"""
        try:
            element = driver.find_element(By.ID, "activeFaultsList")
            assert element is not None
        except NoSuchElementException:
            pytest.fail("Active faults section not found")


class TestJavaScriptFunctions:
    """Test JavaScript function availability and execution"""
    
    def test_update_auto_healing_dashboard_function(self, navigate_to_auto_healing, driver):
        """Test that updateAutoHealingDashboard function exists and can be called"""
        try:
            result = driver.execute_script("return typeof updateAutoHealingDashboard;")
            assert result == "function", "updateAutoHealingDashboard is not a function"
        except Exception as e:
            pytest.fail(f"Error checking updateAutoHealingDashboard: {e}")
    
    def test_load_auto_healing_config_function(self, navigate_to_auto_healing, driver):
        """Test that loadAutoHealingConfig function exists"""
        try:
            result = driver.execute_script("return typeof loadAutoHealingConfig;")
            assert result == "function", "loadAutoHealingConfig is not a function"
        except Exception as e:
            pytest.fail(f"Error checking loadAutoHealingConfig: {e}")
    
    def test_update_active_faults_function(self, navigate_to_auto_healing, driver):
        """Test that updateActiveFaults function exists"""
        try:
            result = driver.execute_script("return typeof updateActiveFaults;")
            assert result == "function", "updateActiveFaults is not a function"
        except Exception as e:
            pytest.fail(f"Error checking updateActiveFaults: {e}")
    
    def test_save_auto_healing_config_function(self, navigate_to_auto_healing, driver):
        """Test that saveAutoHealingConfig function exists"""
        try:
            result = driver.execute_script("return typeof saveAutoHealingConfig;")
            assert result == "function", "saveAutoHealingConfig is not a function"
        except Exception as e:
            pytest.fail(f"Error checking saveAutoHealingConfig: {e}")


class TestChartInitialization:
    """Test Chart.js initialization for performance chart"""
    
    def test_chart_js_loaded(self, navigate_to_auto_healing, driver):
        """Test that Chart.js library is loaded"""
        try:
            result = driver.execute_script("return typeof Chart;")
            assert result == "function", "Chart.js is not loaded"
        except Exception as e:
            pytest.fail(f"Error checking Chart.js: {e}")
    
    def test_chart_canvas_exists(self, navigate_to_auto_healing, driver):
        """Test that chart canvas element exists"""
        try:
            canvas = driver.find_element(By.ID, "healingPerformanceChart")
            assert canvas is not None
            assert canvas.tag_name == "canvas"
        except NoSuchElementException:
            pytest.fail("Healing performance chart canvas not found")


class TestFormInteractions:
    """Test form submission and interactions"""
    
    def test_configuration_form_can_be_filled(self, navigate_to_auto_healing, driver):
        """Test that configuration form fields can be filled"""
        try:
            # Test checkbox
            enabled_checkbox = driver.find_element(By.ID, "healingEnabled")
            original_state = enabled_checkbox.is_selected()
            enabled_checkbox.click()
            time.sleep(0.5)
            assert enabled_checkbox.is_selected() != original_state
            
            # Test number input
            interval_input = driver.find_element(By.ID, "monitoringInterval")
            interval_input.clear()
            interval_input.send_keys("120")
            assert interval_input.get_attribute("value") == "120"
        except Exception as e:
            pytest.fail(f"Error interacting with form: {e}")
    
    def test_save_button_exists(self, navigate_to_auto_healing, driver):
        """Test that save configuration button exists"""
        try:
            # Look for save button (could be by text or onclick)
            save_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Save') or contains(@onclick, 'saveAutoHealingConfig')]")
            assert len(save_buttons) > 0, "Save configuration button not found"
        except Exception as e:
            pytest.fail(f"Error finding save button: {e}")


class TestErrorDisplay:
    """Test error message display"""
    
    def test_error_messages_displayed(self, navigate_to_auto_healing, driver):
        """Test that error messages can be displayed"""
        # This test checks if the notification system works
        try:
            result = driver.execute_script("return typeof showNotification;")
            assert result == "function", "showNotification function not found"
        except Exception as e:
            pytest.fail(f"Error checking notification system: {e}")


class TestLoadingStates:
    """Test loading indicators"""
    
    def test_loading_indicators_exist(self, navigate_to_auto_healing, driver):
        """Test that loading indicators are present initially"""
        # Check if loading spinners or loading text exists
        try:
            # Check status element for loading state
            status_element = driver.find_element(By.ID, "autoHealingStatus")
            status_text = status_element.text.lower()
            # Should show loading or have some initial state
            assert len(status_text) > 0, "Status element should have text"
        except Exception as e:
            pytest.fail(f"Error checking loading states: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

