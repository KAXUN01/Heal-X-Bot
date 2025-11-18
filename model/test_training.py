#!/usr/bin/env python3
"""
Quick test script for the predictive maintenance training pipeline.
Tests the script with minimal configuration for fast validation.
"""

import subprocess
import sys
from pathlib import Path

def test_training():
    """Test the training script with minimal options"""
    script_path = Path(__file__).parent / "train_xgboost_model.py"
    
    print("=" * 80)
    print("Testing Predictive Maintenance Training Script")
    print("=" * 80)
    print()
    
    # Test with minimal options for speed
    cmd = [
        sys.executable,
        str(script_path),
        "--no-tuning",  # Skip hyperparameter tuning for speed
        "--no-shap",    # Skip SHAP for speed
        "--n-iter", "5" # Minimal iterations if tuning is enabled
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print()
        print("=" * 80)
        print("✅ Training test completed successfully!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Check model/artifacts/latest/ for saved model")
        print("2. Review plots in model/artifacts/latest/plots/")
        print("3. Test model_loader.py functions")
        return 0
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print("❌ Training test failed!")
        print("=" * 80)
        print()
        print("Common issues:")
        print("- Missing dependencies: pip install -r requirements.txt")
        print("- Python version: Requires Python 3.8+")
        print("- Check error messages above for details")
        return 1
    except KeyboardInterrupt:
        print()
        print("Test interrupted by user")
        return 1

if __name__ == "__main__":
    sys.exit(test_training())

