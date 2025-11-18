#!/usr/bin/env python3
"""
Example Usage of Predictive Maintenance Model

Demonstrates how to use the trained model for real-time predictions.
"""

import sys
from pathlib import Path

# Add model artifacts to path
model_path = Path(__file__).parent / "artifacts" / "latest"
if not (model_path / "model_loader.py").exists():
    print("ERROR: Model not found. Please train the model first:")
    print("  python3 train_xgboost_model.py")
    sys.exit(1)

sys.path.insert(0, str(model_path))

try:
    from model_loader import (
        predict_anomaly,
        predict_failure_risk,
        predict_time_to_failure,
        get_early_warnings
    )
except ImportError as e:
    print(f"ERROR: Could not import model loader: {e}")
    print("Make sure the model has been trained and artifacts/latest/model_loader.py exists")
    sys.exit(1)

def example_basic_prediction():
    """Example: Basic anomaly prediction"""
    print("=" * 80)
    print("Example 1: Basic Anomaly Prediction")
    print("=" * 80)
    
    # Example system metrics
    metrics = {
        'cpu_percent': 85.0,
        'memory_percent': 90.0,
        'disk_percent': 75.0,
        'network_in_bytes': 1000000,
        'network_out_bytes': 500000,
        'connections_count': 150,
        'memory_available_gb': 2.0,
        'disk_free_gb': 50.0,
        'error_count': 5,
        'warning_count': 10,
        'critical_count': 0,
        'service_failures': 0,
        'auth_failures': 0,
        'ssh_attempts': 0
    }
    
    result = predict_anomaly(metrics)
    print(f"Anomaly Detected: {result.get('is_anomaly', False)}")
    print(f"Anomaly Score: {result.get('anomaly_score', 0):.3f}")
    print(f"Risk Level: {result.get('risk_level', 'Unknown')}")
    print()

def example_failure_risk():
    """Example: Failure risk prediction"""
    print("=" * 80)
    print("Example 2: Failure Risk Prediction")
    print("=" * 80)
    
    metrics = {
        'cpu_percent': 95.0,  # High CPU
        'memory_percent': 92.0,  # High memory
        'disk_percent': 88.0,
        'network_in_bytes': 2000000,
        'network_out_bytes': 1000000,
        'connections_count': 300,
        'memory_available_gb': 0.5,
        'disk_free_gb': 10.0,
        'error_count': 20,  # High error count
        'warning_count': 15,
        'critical_count': 2,
        'service_failures': 1,
        'auth_failures': 0,
        'ssh_attempts': 0
    }
    
    result = predict_failure_risk(metrics)
    print(f"Risk Score: {result.get('risk_score', 0):.3f}")
    print(f"Risk Percentage: {result.get('risk_percentage', 0):.1f}%")
    print(f"Has Early Warning: {result.get('has_early_warning', False)}")
    print(f"Is High Risk: {result.get('is_high_risk', False)}")
    print()

def example_time_to_failure():
    """Example: Time to failure prediction"""
    print("=" * 80)
    print("Example 3: Time to Failure Prediction")
    print("=" * 80)
    
    metrics = {
        'cpu_percent': 88.0,
        'memory_percent': 85.0,
        'disk_percent': 82.0,
        'network_in_bytes': 1500000,
        'network_out_bytes': 800000,
        'connections_count': 200,
        'memory_available_gb': 1.5,
        'disk_free_gb': 20.0,
        'error_count': 12,
        'warning_count': 8,
        'critical_count': 1,
        'service_failures': 0,
        'auth_failures': 0,
        'ssh_attempts': 0
    }
    
    result = predict_time_to_failure(metrics)
    if result.get('hours_until_failure'):
        print(f"Hours Until Failure: {result['hours_until_failure']:.2f}")
        print(f"Predicted Failure Time: {result.get('predicted_failure_time', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'Unknown')}")
    else:
        print("No failure predicted in near future")
        print(f"Message: {result.get('message', 'N/A')}")
    print()

def example_early_warnings():
    """Example: Early warning indicators"""
    print("=" * 80)
    print("Example 4: Early Warning Indicators")
    print("=" * 80)
    
    metrics = {
        'cpu_percent': 92.0,  # Very high
        'memory_percent': 88.0,  # High
        'disk_percent': 95.0,  # Critical
        'network_in_bytes': 3000000,
        'network_out_bytes': 1500000,
        'connections_count': 400,
        'memory_available_gb': 0.3,
        'disk_free_gb': 5.0,
        'error_count': 30,  # High
        'warning_count': 20,
        'critical_count': 3,
        'service_failures': 2,
        'auth_failures': 5,
        'ssh_attempts': 2
    }
    
    result = get_early_warnings(metrics)
    print(f"Warning Count: {result.get('warning_count', 0)}")
    print(f"Has Warnings: {result.get('has_warnings', False)}")
    print()
    
    if result.get('warnings'):
        print("Active Warnings:")
        for i, warning in enumerate(result['warnings'], 1):
            print(f"  {i}. [{warning.get('severity', 'unknown').upper()}] {warning.get('message', 'N/A')}")
    print()

def example_normal_operation():
    """Example: Normal operation (low risk)"""
    print("=" * 80)
    print("Example 5: Normal Operation (Low Risk)")
    print("=" * 80)
    
    metrics = {
        'cpu_percent': 35.0,  # Normal
        'memory_percent': 45.0,  # Normal
        'disk_percent': 60.0,  # Normal
        'network_in_bytes': 500000,
        'network_out_bytes': 250000,
        'connections_count': 50,
        'memory_available_gb': 8.0,
        'disk_free_gb': 100.0,
        'error_count': 0,
        'warning_count': 1,
        'critical_count': 0,
        'service_failures': 0,
        'auth_failures': 0,
        'ssh_attempts': 0
    }
    
    risk = predict_failure_risk(metrics)
    warnings = get_early_warnings(metrics)
    
    print(f"Risk Score: {risk.get('risk_score', 0):.3f} ({risk.get('risk_percentage', 0):.1f}%)")
    print(f"Early Warnings: {warnings.get('warning_count', 0)}")
    print("Status: System operating normally")
    print()

if __name__ == '__main__':
    print()
    print("=" * 80)
    print("Predictive Maintenance Model - Example Usage")
    print("=" * 80)
    print()
    
    try:
        example_basic_prediction()
        example_failure_risk()
        example_time_to_failure()
        example_early_warnings()
        example_normal_operation()
        
        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Integrate these functions into your monitoring dashboard")
        print("2. Set up periodic data collection with collect_training_data.py")
        print("3. Retrain the model periodically with new data")
        print()
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

