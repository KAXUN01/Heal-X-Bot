#!/usr/bin/env python3
"""
Integration Tests - Full Detection → Diagnosis → Healing Cycle
Tests the complete autonomous self-healing system
"""

import sys
import time
import unittest
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'monitoring' / 'server'))

from fault_detector import initialize_fault_detector, get_fault_detector
from fault_injector import initialize_fault_injector, get_fault_injector
from auto_healer import initialize_auto_healer, get_auto_healer
from container_healer import initialize_container_healer, get_container_healer
from root_cause_analyzer import initialize_root_cause_analyzer, get_root_cause_analyzer
from gemini_log_analyzer import initialize_gemini_analyzer

class TestFullCycle(unittest.TestCase):
    """Test the complete detection → diagnosis → healing cycle"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize components for testing"""
        print("\n" + "="*70)
        print("Setting up integration test environment...")
        print("="*70)
        
        # Initialize components
        cls.gemini_analyzer = initialize_gemini_analyzer()
        cls.root_cause_analyzer = initialize_root_cause_analyzer(
            gemini_analyzer=cls.gemini_analyzer
        )
        cls.container_healer = initialize_container_healer()
        cls.auto_healer = initialize_auto_healer(
            gemini_analyzer=cls.gemini_analyzer,
            container_healer=cls.container_healer,
            root_cause_analyzer=cls.root_cause_analyzer
        )
        cls.fault_detector = initialize_fault_detector()
        cls.fault_injector = initialize_fault_injector()
        
        print("✅ Components initialized")
    
    def test_fault_detection(self):
        """Test that faults are detected"""
        print("\n🔍 Testing fault detection...")
        
        # Inject a fault
        success, message = self.fault_injector.inject_service_crash("cloud-sim-api-server")
        self.assertTrue(success, f"Failed to inject fault: {message}")
        
        # Wait for detection
        time.sleep(35)  # Wait for detection interval (30s) + buffer
        
        # Check if fault was detected
        faults = self.fault_detector.get_detected_faults(limit=10)
        self.assertGreater(len(faults), 0, "No faults detected")
        
        # Verify fault type
        detected_fault = faults[-1]
        self.assertEqual(detected_fault.get('type'), 'service_crash')
        print("✅ Fault detection test passed")
    
    def test_root_cause_analysis(self):
        """Test root cause analysis"""
        print("\n🧠 Testing root cause analysis...")
        
        # Create a test fault
        test_fault = {
            'type': 'service_crash',
            'service': 'cloud-sim-api-server',
            'status': 'exited',
            'restart_count': 1,
            'message': 'Container stopped unexpectedly',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'severity': 'critical'
        }
        
        # Analyze fault
        analysis = self.root_cause_analyzer.analyze_fault(test_fault)
        
        self.assertIsNotNone(analysis, "Analysis should not be None")
        self.assertIn('root_cause', analysis, "Analysis should include root_cause")
        self.assertIn('confidence', analysis, "Analysis should include confidence")
        self.assertGreater(analysis.get('confidence', 0), 0, "Confidence should be > 0")
        
        print(f"✅ Root cause analysis test passed (confidence: {analysis.get('confidence', 0):.0%})")
    
    def test_healing_attempt(self):
        """Test healing attempt"""
        print("\n🔧 Testing healing attempt...")
        
        # Create a test fault
        test_fault = {
            'type': 'service_crash',
            'service': 'cloud-sim-api-server',
            'status': 'exited',
            'restart_count': 1,
            'message': 'Container stopped unexpectedly',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'severity': 'critical'
        }
        
        # Attempt healing
        healing_result = self.auto_healer.heal_cloud_fault(test_fault)
        
        self.assertIsNotNone(healing_result, "Healing result should not be None")
        self.assertIn('status', healing_result, "Healing result should include status")
        self.assertIn('actions', healing_result, "Healing result should include actions")
        
        print(f"✅ Healing attempt test passed (status: {healing_result.get('status')})")
    
    def test_manual_instructions_generation(self):
        """Test manual instructions generation"""
        print("\n📖 Testing manual instructions generation...")
        
        test_fault = {
            'type': 'service_crash',
            'service': 'cloud-sim-api-server',
            'status': 'exited',
            'message': 'Container stopped unexpectedly',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'severity': 'critical'
        }
        
        # Generate manual instructions
        instructions = self.auto_healer._generate_manual_instructions(test_fault, None)
        
        self.assertIsNotNone(instructions, "Instructions should not be None")
        self.assertGreater(len(instructions), 0, "Instructions should not be empty")
        self.assertIn('service_crash', instructions.lower() or '', "Instructions should mention service crash")
        
        print("✅ Manual instructions generation test passed")
    
    def test_fault_statistics(self):
        """Test fault statistics"""
        print("\n📊 Testing fault statistics...")
        
        stats = self.fault_detector.get_fault_statistics()
        
        self.assertIsNotNone(stats, "Statistics should not be None")
        self.assertIn('total_faults', stats, "Statistics should include total_faults")
        self.assertIn('monitoring_active', stats, "Statistics should include monitoring_active")
        
        print(f"✅ Fault statistics test passed (total: {stats.get('total_faults', 0)})")
    
    def test_healing_statistics(self):
        """Test healing statistics"""
        print("\n📊 Testing healing statistics...")
        
        stats = self.auto_healer.get_healing_statistics()
        
        self.assertIsNotNone(stats, "Statistics should not be None")
        self.assertIn('total_attempts', stats, "Statistics should include total_attempts")
        self.assertIn('success_rate', stats, "Statistics should include success_rate")
        
        print(f"✅ Healing statistics test passed (success rate: {stats.get('success_rate', 0)}%)")

def run_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("🧪 INTEGRATION TESTS - FULL CYCLE")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFullCycle)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {len(result.failures)} TEST(S) FAILED")
        print(f"   {len(result.errors)} ERROR(S)")
    print("="*70 + "\n")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

