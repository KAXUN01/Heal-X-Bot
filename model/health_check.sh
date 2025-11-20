#!/bin/bash
"""
Health Check Script for Predictive Maintenance Model

Returns exit code:
  0 = Model healthy
  1 = Model warning (degraded but functional)
  2 = Model critical (not working)
"""

MODEL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS_DIR="$MODEL_DIR/artifacts/latest"

# Check if model exists
if [ ! -f "$ARTIFACTS_DIR/model_loader.py" ]; then
    echo "CRITICAL: Model not found at $ARTIFACTS_DIR"
    exit 2
fi

# Check if required files exist
REQUIRED_FILES=("scaler.pkl" "feature_names.json" "metrics.json")
MISSING_FILES=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$ARTIFACTS_DIR/$file" ]; then
        echo "WARNING: Missing file: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo "WARNING: Model may not function correctly (missing $MISSING_FILES files)"
    exit 1
fi

# Try to verify model works
cd "$MODEL_DIR"
python3 verify_model.py > /dev/null 2>&1
VERIFY_EXIT=$?

if [ $VERIFY_EXIT -eq 0 ]; then
    echo "OK: Model is healthy and functional"
    exit 0
elif [ $VERIFY_EXIT -eq 1 ]; then
    echo "WARNING: Model verification failed"
    exit 1
else
    echo "CRITICAL: Model verification error"
    exit 2
fi

