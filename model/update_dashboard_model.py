#!/usr/bin/env python3
"""
Update Dashboard with Latest Model

This script ensures the dashboard is using the latest trained model.
Can be run after model retraining to refresh the dashboard.
"""

import sys
import requests
import time
from pathlib import Path

def check_dashboard_health(base_url: str = "http://localhost:5001") -> bool:
    """Check if dashboard API is healthy"""
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def reload_model(base_url: str = "http://localhost:5001") -> bool:
    """Trigger model reload (if API supports it)"""
    try:
        # Try to trigger a model reload by calling the endpoint
        # The API should auto-reload from artifacts/latest/
        response = requests.get(f"{base_url}/api/predict-failure-risk", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data or 'not available' not in data.get('error', '').lower():
                return True
    except Exception as e:
        print(f"Error checking model: {e}")
    return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update dashboard with latest model')
    parser.add_argument('--dashboard-url', type=str, default='http://localhost:5001',
                       help='Dashboard API URL')
    parser.add_argument('--wait', type=int, default=5,
                       help='Wait time in seconds for dashboard to be ready')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Updating Dashboard with Latest Model")
    print("=" * 80)
    print()
    
    # Check if model exists
    artifacts_dir = Path(__file__).parent / "artifacts" / "latest"
    if not (artifacts_dir / "model_loader.py").exists():
        print("❌ ERROR: No model found in artifacts/latest/")
        print("   Train a model first: python3 train_xgboost_model.py")
        return 1
    
    print("✅ Latest model found")
    
    # Wait for dashboard to be ready
    print(f"Waiting for dashboard to be ready (max {args.wait}s)...")
    for i in range(args.wait):
        if check_dashboard_health(args.dashboard_url):
            print("✅ Dashboard is healthy")
            break
        time.sleep(1)
    else:
        print("⚠️  WARNING: Dashboard may not be ready")
        print(f"   Check: {args.dashboard_url}/api/health")
    
    # Test model loading
    print()
    print("Testing model in dashboard...")
    if reload_model(args.dashboard_url):
        print("✅ Model is loaded and working in dashboard")
        print()
        print("Dashboard endpoints ready:")
        print(f"  - {args.dashboard_url}/api/predict-failure-risk")
        print(f"  - {args.dashboard_url}/api/get-early-warnings")
        print(f"  - {args.dashboard_url}/api/predict-time-to-failure")
        return 0
    else:
        print("⚠️  WARNING: Model may not be loaded in dashboard")
        print("   The dashboard API should auto-reload from artifacts/latest/")
        print("   Try restarting the dashboard service if needed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

