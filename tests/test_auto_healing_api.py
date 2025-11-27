"""
Comprehensive test suite for Auto-Healing API endpoints
Tests all auto-healing related endpoints, error handling, and edge cases
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path to import the API
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from monitoring.server.healing_dashboard_api import app
except ImportError:
    # Try alternative import path
    sys.path.insert(0, str(Path(__file__).parent.parent / "monitoring" / "server"))
    from healing_dashboard_api import app

client = TestClient(app)


class TestHealingHistoryAPI:
    """Test suite for /api/cloud/healing/history endpoint"""
    
    def test_get_healing_history_success(self):
        """Test successful retrieval of healing history"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer') as mock_healer:
            mock_healer.get_healing_history.return_value = [
                {
                    "id": 1,
                    "timestamp": "2024-01-01T00:00:00",
                    "status": "healed",
                    "error": {"type": "service_crash", "service": "test-service"},
                    "actions": [{"action": "restart_service", "success": True}]
                }
            ]
            mock_healer.get_healing_statistics.return_value = {
                "total_healings": 1,
                "success_rate": 1.0,
                "total_attempts": 1,
                "successful": 1,
                "failed": 0
            }
            
            response = client.get("/api/cloud/healing/history?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "history" in data
            assert "statistics" in data
            assert len(data["history"]) == 1
    
    def test_get_healing_history_no_healer(self):
        """Test response when auto-healer is not initialized"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer', None):
            response = client.get("/api/cloud/healing/history")
            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    def test_get_healing_history_empty(self):
        """Test response when no healing history exists"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer') as mock_healer:
            mock_healer.get_healing_history.return_value = []
            mock_healer.get_healing_statistics.return_value = {}
            
            response = client.get("/api/cloud/healing/history")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["history"] == []
    
    def test_get_healing_history_with_limit(self):
        """Test healing history with custom limit"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer') as mock_healer:
            mock_healer.get_healing_history.return_value = []
            mock_healer.get_healing_statistics.return_value = {}
            
            response = client.get("/api/cloud/healing/history?limit=50")
            assert response.status_code == 200
            mock_healer.get_healing_history.assert_called_with(limit=50)


class TestAutoHealerStatusAPI:
    """Test suite for /api/auto-healer/status endpoint"""
    
    def test_get_status_success(self):
        """Test successful retrieval of auto-healer status"""
        mock_healer = Mock()
        mock_healer.enabled = True
        mock_healer.auto_execute = True
        mock_healer.running = True
        mock_healer.max_healing_attempts = 3
        mock_healer.monitoring_interval = 60
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', mock_healer):
            response = client.get("/api/auto-healer/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "auto_healer" in data
            assert data["auto_healer"]["enabled"] is True
            assert data["auto_healer"]["monitoring"] is True
    
    def test_get_status_no_healer(self):
        """Test response when auto-healer is not initialized"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer', None):
            response = client.get("/api/auto-healer/status")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "error"
            assert "message" in data


class TestAutoHealerConfigAPI:
    """Test suite for /api/auto-healer/config endpoint"""
    
    def test_update_config_success(self):
        """Test successful configuration update"""
        mock_healer = Mock()
        mock_healer.update_config.return_value = {
            "enabled": True,
            "auto_execute": True,
            "max_healing_attempts": 5,
            "monitoring_interval": 120
        }
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', mock_healer):
            response = client.post(
                "/api/auto-healer/config",
                json={
                    "enabled": True,
                    "auto_execute": True,
                    "max_attempts": 5,
                    "monitoring_interval": 120
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "auto_healer" in data
    
    def test_update_config_no_healer(self):
        """Test configuration update when auto-healer is not initialized"""
        with patch('monitoring.server.healing_dashboard_api.auto_healer', None):
            response = client.post(
                "/api/auto-healer/config",
                json={"enabled": True}
            )
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "error"
    
    def test_update_config_partial(self):
        """Test partial configuration update"""
        mock_healer = Mock()
        mock_healer.update_config.return_value = {"enabled": False}
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', mock_healer):
            response = client.post(
                "/api/auto-healer/config",
                json={"enabled": False}
            )
            assert response.status_code == 200
            mock_healer.update_config.assert_called_once()
    
    def test_update_config_invalid_value(self):
        """Test configuration update with invalid values"""
        mock_healer = Mock()
        mock_healer.update_config.side_effect = ValueError("Invalid monitoring interval")
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', mock_healer):
            response = client.post(
                "/api/auto-healer/config",
                json={"monitoring_interval": -1}
            )
            assert response.status_code == 200  # Returns 200 with error status
            data = response.json()
            assert data["status"] == "error"


class TestFaultsAPI:
    """Test suite for /api/cloud/faults endpoint"""
    
    def test_get_faults_success(self):
        """Test successful retrieval of detected faults"""
        with patch('monitoring.server.healing_dashboard_api.fault_detector') as mock_detector:
            mock_detector.get_detected_faults.return_value = [
                {
                    "id": 1,
                    "type": "service_crash",
                    "service": "test-service",
                    "severity": "critical",
                    "timestamp": "2024-01-01T00:00:00",
                    "reason": "Service crashed unexpectedly"
                }
            ]
            mock_detector.get_fault_statistics.return_value = {
                "total_faults": 1,
                "critical": 1
            }
            
            response = client.get("/api/cloud/faults?limit=10")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "faults" in data
            assert len(data["faults"]) == 1
    
    def test_get_faults_no_detector(self):
        """Test response when fault detector is not initialized"""
        with patch('monitoring.server.healing_dashboard_api.fault_detector', None):
            response = client.get("/api/cloud/faults")
            assert response.status_code == 503
            data = response.json()
            assert data["success"] is False
            assert "faults" in data
            assert data["faults"] == []
    
    def test_get_faults_empty(self):
        """Test response when no faults are detected"""
        with patch('monitoring.server.healing_dashboard_api.fault_detector') as mock_detector:
            mock_detector.get_detected_faults.return_value = []
            mock_detector.get_fault_statistics.return_value = {}
            
            response = client.get("/api/cloud/faults")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["faults"] == []


class TestFaultHealingAPI:
    """Test suite for /api/cloud/faults/{fault_id}/heal endpoint"""
    
    def test_heal_fault_success(self):
        """Test successful fault healing"""
        mock_healer = Mock()
        mock_healer.heal_cloud_fault.return_value = {
            "success": True,
            "status": "healed",
            "actions": [{"action": "restart_service", "success": True}]
        }
        
        mock_detector = Mock()
        mock_detector.get_detected_faults.return_value = [
            {"id": 1, "type": "service_crash", "service": "test-service"}
        ]
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', mock_healer), \
             patch('monitoring.server.healing_dashboard_api.fault_detector', mock_detector):
            response = client.post("/api/cloud/faults/0/heal")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "healing_result" in data
    
    def test_heal_fault_not_found(self):
        """Test healing non-existent fault"""
        mock_detector = Mock()
        mock_detector.get_detected_faults.return_value = []
        
        with patch('monitoring.server.healing_dashboard_api.auto_healer', Mock()), \
             patch('monitoring.server.healing_dashboard_api.fault_detector', mock_detector):
            response = client.post("/api/cloud/faults/999/heal")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data


class TestFaultInjectionAPI:
    """Test suite for /api/cloud/faults/inject endpoint"""
    
    def test_inject_fault_success(self):
        """Test successful fault injection"""
        mock_injector = Mock()
        mock_injector.inject_service_crash.return_value = (True, "Fault injected successfully")
        
        with patch('monitoring.server.healing_dashboard_api.fault_injector', mock_injector):
            response = client.post(
                "/api/cloud/faults/inject",
                json={"type": "crash", "container": "test-container"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_inject_fault_no_injector(self):
        """Test fault injection when injector is not initialized"""
        with patch('monitoring.server.healing_dashboard_api.fault_injector', None):
            response = client.post(
                "/api/cloud/faults/inject",
                json={"type": "crash"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    def test_inject_fault_invalid_type(self):
        """Test fault injection with invalid fault type"""
        mock_injector = Mock()
        
        with patch('monitoring.server.healing_dashboard_api.fault_injector', mock_injector):
            response = client.post(
                "/api/cloud/faults/inject",
                json={"type": "invalid_type"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

