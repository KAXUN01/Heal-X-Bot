#!/usr/bin/env python3
"""
Automated Model Retraining Script

Schedules periodic retraining of the predictive maintenance model with new data.
Can be run as a cron job or systemd service.
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automated_retraining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_data_available(data_dir: Path, min_samples: int = 1000) -> bool:
    """Check if enough training data is available"""
    if not data_dir.exists():
        return False
    
    # Find CSV files
    csv_files = list(data_dir.glob("system_metrics_*.csv"))
    if not csv_files:
        return False
    
    # Check total samples
    total_samples = 0
    for csv_file in csv_files:
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            total_samples += len(df)
        except Exception as e:
            logger.warning(f"Error reading {csv_file}: {e}")
    
    logger.info(f"Found {total_samples} total samples in {len(csv_files)} files")
    return total_samples >= min_samples

def get_latest_model_metrics(artifacts_dir: Path) -> dict:
    """Get metrics from the latest trained model"""
    latest_dir = artifacts_dir / "latest"
    metrics_path = latest_dir / "metrics.json"
    
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading metrics: {e}")
    
    return {}

def should_retrain(artifacts_dir: Path, min_accuracy: float = 0.85, 
                   days_since_training: int = 7) -> bool:
    """Determine if model should be retrained"""
    latest_dir = artifacts_dir / "latest"
    config_path = latest_dir / "config.json"
    
    if not config_path.exists():
        logger.info("No existing model found - retraining recommended")
        return True
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check training timestamp
        train_time = datetime.fromisoformat(config.get('timestamp', ''))
        days_old = (datetime.now() - train_time).days
        
        if days_old >= days_since_training:
            logger.info(f"Model is {days_old} days old - retraining recommended")
            return True
        
        # Check model performance
        metrics = get_latest_model_metrics(artifacts_dir)
        accuracy = metrics.get('accuracy', 0)
        
        if accuracy < min_accuracy:
            logger.info(f"Model accuracy ({accuracy:.3f}) below threshold ({min_accuracy}) - retraining recommended")
            return True
        
        logger.info(f"Model is recent ({days_old} days) and performing well (accuracy: {accuracy:.3f})")
        return False
        
    except Exception as e:
        logger.warning(f"Error checking model status: {e}")
        return True

def retrain_model(data_dir: Path = None, enable_regression: bool = True,
                  no_tuning: bool = False, no_shap: bool = True) -> bool:
    """Retrain the model"""
    script_path = Path(__file__).parent / "train_xgboost_model.py"
    
    cmd = [sys.executable, str(script_path)]
    
    if data_dir:
        # Find latest CSV file
        csv_files = sorted(data_dir.glob("system_metrics_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if csv_files:
            cmd.extend(["--data-path", str(csv_files[0])])
            logger.info(f"Using training data: {csv_files[0]}")
    
    if enable_regression:
        cmd.append("--enable-regression")
    
    if no_tuning:
        cmd.append("--no-tuning")
    
    if no_shap:
        cmd.append("--no-shap")
    
    logger.info(f"Starting model retraining: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("Model retraining completed successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Model retraining failed with return code {result.returncode}")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Model retraining timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Error during model retraining: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Automated model retraining')
    parser.add_argument('--data-dir', type=str, default=None,
                       help='Directory containing training data CSV files')
    parser.add_argument('--artifacts-dir', type=str, default=None,
                       help='Artifacts directory (default: model/artifacts)')
    parser.add_argument('--force', action='store_true',
                       help='Force retraining even if not needed')
    parser.add_argument('--min-samples', type=int, default=1000,
                       help='Minimum samples required for training')
    parser.add_argument('--min-accuracy', type=float, default=0.85,
                       help='Minimum accuracy threshold')
    parser.add_argument('--days-since-training', type=int, default=7,
                       help='Days since last training to trigger retraining')
    parser.add_argument('--no-regression', action='store_true',
                       help='Skip regression model training')
    parser.add_argument('--enable-tuning', action='store_true',
                       help='Enable hyperparameter tuning')
    parser.add_argument('--enable-shap', action='store_true',
                       help='Enable SHAP explanations')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Automated Model Retraining")
    logger.info("=" * 80)
    
    # Set default paths
    if args.data_dir is None:
        args.data_dir = Path(__file__).parent / "training_data"
    else:
        args.data_dir = Path(args.data_dir)
    
    if args.artifacts_dir is None:
        args.artifacts_dir = Path(__file__).parent / "artifacts"
    else:
        args.artifacts_dir = Path(args.artifacts_dir)
    
    # Check if retraining is needed
    if not args.force:
        if not should_retrain(args.artifacts_dir, args.min_accuracy, args.days_since_training):
            logger.info("Retraining not needed at this time")
            return 0
        
        if not check_data_available(args.data_dir, args.min_samples):
            logger.warning(f"Not enough training data (minimum: {args.min_samples} samples)")
            logger.info("Run collect_training_data.py to gather more data")
            return 1
    
    # Retrain model
    success = retrain_model(
        data_dir=args.data_dir if args.data_dir.exists() else None,
        enable_regression=not args.no_regression,
        no_tuning=not args.enable_tuning,
        no_shap=not args.enable_shap
    )
    
    if success:
        logger.info("=" * 80)
        logger.info("Retraining completed successfully")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("=" * 80)
        logger.error("Retraining failed")
        logger.error("=" * 80)
        return 1

if __name__ == '__main__':
    sys.exit(main())

