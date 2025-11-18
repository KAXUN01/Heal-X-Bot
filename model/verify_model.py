#!/usr/bin/env python3
"""
Model Verification Script

Verifies that the trained model is working correctly and can make predictions.
"""

import sys
from pathlib import Path
import json

def verify_model():
    """Verify model is loaded and working"""
    print("=" * 80)
    print("Predictive Maintenance Model Verification")
    print("=" * 80)
    print()
    
    # Check if model exists
    artifacts_dir = Path(__file__).parent / "artifacts" / "latest"
    model_loader_path = artifacts_dir / "model_loader.py"
    
    if not model_loader_path.exists():
        print("❌ ERROR: Model not found!")
        print(f"   Expected: {model_loader_path}")
        print()
        print("   Solution: Train the model first:")
        print("   python3 train_xgboost_model.py --no-tuning --no-shap")
        return 1
    
    print("✅ Model loader found")
    
    # Check required files
    required_files = {
        "model.json": "Classification model",
        "model.pkl": "Classification model (fallback)",
        "scaler.pkl": "Feature scaler",
        "feature_names.json": "Feature names",
        "metrics.json": "Model metrics",
        "config.json": "Model configuration"
    }
    
    missing_files = []
    for file_name, description in required_files.items():
        file_path = artifacts_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} found")
        else:
            print(f"⚠️  {file_name} missing ({description})")
            missing_files.append(file_name)
    
    if missing_files:
        print()
        print(f"⚠️  Warning: {len(missing_files)} file(s) missing")
        print("   Model may not work correctly")
    
    # Try to load and test model
    print()
    print("Testing model loading...")
    try:
        sys.path.insert(0, str(artifacts_dir))
        from model_loader import (
            predict_anomaly,
            predict_failure_risk,
            get_early_warnings
        )
        print("✅ Model loader imported successfully")
        
        # Test with sample metrics
        print()
        print("Testing predictions with sample metrics...")
        sample_metrics = {
            'cpu_percent': 75.0,
            'memory_percent': 80.0,
            'disk_percent': 70.0,
            'network_in_bytes': 1000000,
            'network_out_bytes': 500000,
            'connections_count': 100,
            'memory_available_gb': 4.0,
            'disk_free_gb': 50.0,
            'error_count': 2,
            'warning_count': 5,
            'critical_count': 0,
            'service_failures': 0,
            'auth_failures': 0,
            'ssh_attempts': 0
        }
        
        # Test anomaly prediction
        result = predict_anomaly(sample_metrics)
        if 'error' in result:
            print(f"❌ Anomaly prediction failed: {result['error']}")
            return 1
        print(f"✅ Anomaly prediction: {result.get('is_anomaly', False)} (score: {result.get('anomaly_score', 0):.3f})")
        
        # Test risk prediction
        risk = predict_failure_risk(sample_metrics)
        if 'error' in risk:
            print(f"❌ Risk prediction failed: {risk['error']}")
            return 1
        print(f"✅ Risk prediction: {risk.get('risk_percentage', 0):.1f}%")
        
        # Test warnings
        warnings = get_early_warnings(sample_metrics)
        if 'error' in warnings:
            print(f"❌ Warnings failed: {warnings['error']}")
            return 1
        print(f"✅ Early warnings: {warnings.get('warning_count', 0)} active")
        
        # Load metrics
        metrics_path = artifacts_dir / "metrics.json"
        if metrics_path.exists():
            with open(metrics_path) as f:
                metrics = json.load(f)
            print()
            print("Model Performance Metrics:")
            print(f"  Accuracy: {metrics.get('accuracy', 0):.4f}")
            print(f"  Precision: {metrics.get('precision', 0):.4f}")
            print(f"  Recall: {metrics.get('recall', 0):.4f}")
            print(f"  F1 Score: {metrics.get('f1_score', 0):.4f}")
            print(f"  ROC-AUC: {metrics.get('roc_auc', 0):.4f}")
            if 'early_detection_rate' in metrics:
                print(f"  Early Detection Rate: {metrics['early_detection_rate']:.2%}")
        
        print()
        print("=" * 80)
        print("✅ Model verification PASSED")
        print("=" * 80)
        print()
        print("Model is ready for use!")
        print("  - API endpoints: /api/predict-failure-risk, /api/get-early-warnings")
        print("  - Dashboard: http://localhost:3001 → Predictive Maintenance tab")
        return 0
        
    except ImportError as e:
        print(f"❌ ERROR: Could not import model loader: {e}")
        print()
        print("   Solution: Train the model first:")
        print("   python3 train_xgboost_model.py")
        return 1
    except Exception as e:
        print(f"❌ ERROR: Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(verify_model())

