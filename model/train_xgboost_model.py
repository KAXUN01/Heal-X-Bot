#!/usr/bin/env python3
"""
Advanced XGBoost Training Pipeline for Predictive Maintenance & Proactive Intelligence

This script trains a predictive model using XGBoost (with GradientBoosting fallback)
for Ubuntu system anomaly detection with predictive maintenance capabilities.
Predicts system failures BEFORE they occur with comprehensive feature engineering,
evaluation, and artifact management for real-time dashboard integration.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, roc_curve, precision_recall_curve
)
from sklearn.ensemble import GradientBoostingClassifier
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

# Try to import XGBoost, fallback to GradientBoosting
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available, will use GradientBoostingClassifier")

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available, SHAP explanations will be skipped")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# System metrics feature names for predictive maintenance
SYSTEM_METRIC_FEATURES = [
    "cpu_percent", "memory_percent", "disk_percent",
    "network_in_bytes", "network_out_bytes", "connections_count",
    "memory_available_gb", "disk_free_gb"
]

# Log pattern features
LOG_PATTERN_FEATURES = [
    "error_count", "warning_count", "critical_count",
    "service_failures", "auth_failures", "ssh_attempts"
]


class DataLoader:
    """Load data from system logs, monitoring API, or generate synthetic data with predictive labeling"""
    
    def __init__(self, data_path: Optional[str] = None, prediction_horizon: List[int] = [1, 6, 24]):
        self.data_path = data_path
        self.project_root = Path(__file__).parent.parent
        self.prediction_horizon = prediction_horizon  # Hours ahead to predict
        
    def load_from_logs(self) -> Optional[pd.DataFrame]:
        """Load data from system logs with failure timeline reconstruction"""
        log_paths = [
            self.project_root / "logs" / "centralized" / "centralized.json",
            self.project_root / "logs" / "fluent-bit" / "fluent-bit-output.jsonl"
        ]
        
        records = []
        for log_path in log_paths:
            if log_path.exists():
                logger.info(f"Loading data from {log_path}")
                try:
                    with open(log_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    entry = json.loads(line)
                                    records.append(self._extract_features_from_log(entry))
                                except json.JSONDecodeError:
                                    continue
                except Exception as e:
                    logger.warning(f"Error reading {log_path}: {e}")
        
        if not records:
            return None
        
        df = pd.DataFrame(records)
        if len(df) < 100:
            logger.warning(f"Only {len(df)} records found, generating synthetic data instead")
            return None
        
        # Add predictive labels (time until failure)
        df = self._add_predictive_labels(df)
        logger.info(f"Loaded {len(df)} records from logs")
        return df
    
    def _extract_features_from_log(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract system features from log entry"""
        timestamp = entry.get('timestamp', entry.get('@timestamp', datetime.now().isoformat()))
        metrics = entry.get('metrics', {})
        message = entry.get('message', '')
        level = entry.get('level', '').upper()
        
        record = {
            'timestamp': timestamp,
            # System metrics
            'cpu_percent': float(metrics.get('cpu', metrics.get('cpu_percent', 0))),
            'memory_percent': float(metrics.get('memory', metrics.get('memory_percent', 0))),
            'disk_percent': float(metrics.get('disk', metrics.get('disk_percent', 0))),
            'network_in_bytes': float(metrics.get('network_in', metrics.get('network_in_bytes', 0))),
            'network_out_bytes': float(metrics.get('network_out', metrics.get('network_out_bytes', 0))),
            'connections_count': float(metrics.get('connections', metrics.get('connections_count', 0))),
            'memory_available_gb': float(metrics.get('memory_available', metrics.get('memory_available_gb', 0))),
            'disk_free_gb': float(metrics.get('disk_free', metrics.get('disk_free_gb', 0))),
            # Log patterns
            'error_count': 1 if level in ['ERROR', 'CRITICAL', 'ALERT'] else 0,
            'warning_count': 1 if level == 'WARNING' else 0,
            'critical_count': 1 if level in ['CRITICAL', 'ALERT'] else 0,
            'service_failures': 1 if any(kw in message.lower() for kw in ['failed', 'crash', 'down', 'stopped']) else 0,
            'auth_failures': 1 if any(kw in message.lower() for kw in ['authentication', 'login failed', 'unauthorized']) else 0,
            'ssh_attempts': 1 if 'ssh' in message.lower() and ('failed' in message.lower() or 'attempt' in message.lower()) else 0
        }
        
        return record
    
    def _add_predictive_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add predictive labels: target (will fail) and time_until_failure (hours)"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Identify failure events (critical errors, service failures, resource exhaustion)
        df['is_failure'] = (
            (df['critical_count'] > 0) |
            (df['service_failures'] > 0) |
            (df['cpu_percent'] > 95) |
            (df['memory_percent'] > 95) |
            (df['disk_percent'] > 95)
        ).astype(int)
        
        # Calculate time until next failure for each point
        df['time_until_failure'] = np.nan
        failure_indices = df[df['is_failure'] == 1].index
        
        for idx in df.index:
            future_failures = failure_indices[failure_indices > idx]
            if len(future_failures) > 0:
                next_failure_idx = future_failures[0]
                time_diff = (df.loc[next_failure_idx, 'timestamp'] - df.loc[idx, 'timestamp']).total_seconds() / 3600
                df.loc[idx, 'time_until_failure'] = time_diff
        
        # Create target: will fail within prediction horizon (default 24h)
        max_horizon = max(self.prediction_horizon)
        df['target'] = ((df['time_until_failure'] <= max_horizon) & (df['time_until_failure'] > 0)).astype(int)
        
        # Fill NaN time_until_failure with large value (no failure in horizon)
        df['time_until_failure'] = df['time_until_failure'].fillna(max_horizon * 2)
        
        return df
    
    def generate_synthetic_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic system metrics data with temporal failure patterns"""
        logger.info(f"Generating {n_samples} synthetic samples with failure patterns")
        
        np.random.seed(42)
        data = []
        base_time = datetime.now() - timedelta(days=30)
        
        # Generate failure events (5% of samples will have failures)
        n_failures = int(n_samples * 0.05)
        failure_times = sorted(np.random.choice(n_samples, n_failures, replace=False))
        
        for i in range(n_samples):
            timestamp = base_time + timedelta(seconds=i * 60)  # 1 minute intervals
            
            # Determine if failure is coming (within 24h)
            time_to_failure = None
            is_failure_coming = False
            
            for fail_idx in failure_times:
                if fail_idx > i:
                    hours_until = (fail_idx - i) * (1/60)  # Convert minutes to hours
                    if hours_until <= 24:
                        time_to_failure = hours_until
                        is_failure_coming = True
                        break
            
            # Generate features with degradation patterns before failures
            if is_failure_coming and time_to_failure is not None:
                # Degradation pattern: metrics worsen as failure approaches
                degradation_factor = 1.0 - (time_to_failure / 24.0)  # 0 to 1
                
                cpu_base = 30 + degradation_factor * 60  # CPU increases to 90%+
                memory_base = 40 + degradation_factor * 50  # Memory increases to 90%+
                disk_base = 50 + degradation_factor * 40  # Disk increases to 90%+
                error_rate = degradation_factor * 10  # Error count increases
            else:
                # Normal operation
                cpu_base = np.random.uniform(10, 50)
                memory_base = np.random.uniform(20, 60)
                disk_base = np.random.uniform(30, 70)
                error_rate = np.random.uniform(0, 2)
            
            record = {
                'timestamp': timestamp.isoformat(),
                'cpu_percent': np.clip(cpu_base + np.random.normal(0, 5), 0, 100),
                'memory_percent': np.clip(memory_base + np.random.normal(0, 5), 0, 100),
                'disk_percent': np.clip(disk_base + np.random.normal(0, 3), 0, 100),
                'network_in_bytes': np.random.uniform(1000, 1000000),
                'network_out_bytes': np.random.uniform(1000, 1000000),
                'connections_count': np.random.uniform(10, 500),
                'memory_available_gb': np.random.uniform(1, 16),
                'disk_free_gb': np.random.uniform(10, 100),
                'error_count': int(np.random.poisson(error_rate)),
                'warning_count': int(np.random.poisson(error_rate * 0.5)),
                'critical_count': 1 if is_failure_coming and time_to_failure < 1 else 0,
                'service_failures': 1 if is_failure_coming and time_to_failure < 2 else 0,
                'auth_failures': int(np.random.poisson(0.1)),
                'ssh_attempts': int(np.random.poisson(0.05)),
                'is_failure': 1 if i in failure_times else 0,
                'time_until_failure': time_to_failure if time_to_failure is not None else 48.0,
                'target': 1 if is_failure_coming else 0
            }
            
            data.append(record)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated synthetic dataset: {len(df)} samples, {df['target'].sum()} with upcoming failures, {df['is_failure'].sum()} actual failures")
        return df
    
    def load_from_api(self) -> Optional[pd.DataFrame]:
        """Load data from monitoring API (if available)"""
        try:
            import requests
            api_url = "http://localhost:5000/api/metrics_history"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df = self._add_predictive_labels(df)
                logger.info(f"Loaded {len(df)} records from monitoring API")
                return df
        except Exception as e:
            logger.debug(f"Could not load from API: {e}")
        return None
    
    def load_data(self) -> pd.DataFrame:
        """Load data from CSV, logs, API, or generate synthetic"""
        if self.data_path and Path(self.data_path).exists():
            logger.info(f"Loading data from {self.data_path}")
            df = pd.read_csv(self.data_path)
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.date_range(start=datetime.now() - timedelta(days=len(df)), periods=len(df), freq='1min')
            if 'target' not in df.columns or 'time_until_failure' not in df.columns:
                df = self._add_predictive_labels(df)
            return df
        
        # Try to load from API
        df = self.load_from_api()
        if df is not None:
            return df
        
        # Try to load from logs
        df = self.load_from_logs()
        if df is not None:
            return df
        
        # Generate synthetic data
        return self.generate_synthetic_data()


class FeatureEngineer:
    """Feature engineering with time-windowed aggregations"""
    
    def __init__(self, auto_detect_windows: bool = True):
        self.auto_detect_windows = auto_detect_windows
        self.optimal_windows = []
        self.feature_names = []
    
    def _auto_detect_windows(self, df: pd.DataFrame, target_col: str = 'target') -> List[str]:
        """Auto-detect optimal time windows using correlation analysis"""
        logger.info("Auto-detecting optimal time windows...")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Candidate windows
        windows = ['1min', '5min', '15min', '1h', '6h', '24h']
        window_scores = {}
        
        # Calculate mutual information/correlation for each window
        for window in windows:
            try:
                # Create rolling features
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if target_col in numeric_cols:
                    numeric_cols.remove(target_col)
                
                if not numeric_cols:
                    continue
                
                # Set timestamp as index for rolling
                df_temp = df.set_index('timestamp')
                # Calculate rolling statistics
                rolling = df_temp[numeric_cols].rolling(window=window, min_periods=1)
                rolling_mean = rolling.mean()
                
                # Calculate correlation with target
                correlations = []
                for col in rolling_mean.columns:
                    if col != target_col:
                        corr = abs(rolling_mean[col].corr(df[target_col]))
                        if not np.isnan(corr):
                            correlations.append(corr)
                
                if correlations:
                    window_scores[window] = np.mean(correlations)
            except Exception as e:
                logger.debug(f"Error processing window {window}: {e}")
                continue
        
        # Select top 3 windows
        if window_scores:
            sorted_windows = sorted(window_scores.items(), key=lambda x: x[1], reverse=True)
            optimal = [w[0] for w in sorted_windows[:3]]
            logger.info(f"Selected optimal windows: {optimal}")
            return optimal
        
        # Default windows
        return ['5min', '15min', '1h']
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create temporal features including time since last failure"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Extract time components
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        
        # Time since last event
        df['time_since_last'] = df['timestamp'].diff().dt.total_seconds().fillna(0)
        
        # Time since last failure (if available)
        if 'is_failure' in df.columns:
            failure_times = df[df['is_failure'] == 1]['timestamp']
            if len(failure_times) > 0:
                df['time_since_last_failure'] = df['timestamp'].apply(
                    lambda t: (t - failure_times[failure_times < t].max()).total_seconds() / 3600
                    if len(failure_times[failure_times < t]) > 0 else np.nan
                )
                df['time_since_last_failure'] = df['time_since_last_failure'].fillna(df['time_since_last_failure'].max() if df['time_since_last_failure'].notna().any() else 0)
        
        return df
    
    def create_windowed_features(self, df: pd.DataFrame, windows: List[str]) -> pd.DataFrame:
        """Create rolling window features with trend and acceleration analysis"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Set timestamp as index for rolling operations
        df_indexed = df.set_index('timestamp')
        
        # Get numeric columns (excluding target, timestamp, and time_until_failure for features)
        numeric_cols = df_indexed.select_dtypes(include=[np.number]).columns.tolist()
        exclude_cols = ['target', 'class', 'time_until_failure', 'is_failure']
        for col in exclude_cols:
            if col in numeric_cols:
                numeric_cols.remove(col)
        
        # Key metrics for trend analysis
        key_metrics = ['cpu_percent', 'memory_percent', 'disk_percent', 'error_count', 'warning_count']
        available_metrics = [m for m in key_metrics if m in numeric_cols]
        
        for window in windows:
            try:
                # Use time-based rolling window
                rolling = df_indexed[numeric_cols].rolling(window=window, min_periods=1)
                
                # Basic rolling statistics
                rolling_mean = rolling.mean()
                rolling_std = rolling.std()
                
                # Add aggregated statistics
                df[f'{window}_mean_agg'] = rolling_mean.mean(axis=1).values
                df[f'{window}_std_agg'] = rolling_std.mean(axis=1).values
                df[f'{window}_min_agg'] = rolling.min().min(axis=1).values
                df[f'{window}_max_agg'] = rolling.max().max(axis=1).values
                
                # Trend analysis for key metrics (rate of change)
                for metric in available_metrics:
                    if metric in rolling_mean.columns:
                        # Calculate trend (slope) over window
                        metric_values = df_indexed[metric]
                        trend = metric_values.diff().rolling(window=window, min_periods=1).mean()
                        df[f'{metric}_{window}_trend'] = trend.values
                        
                        # Acceleration (second derivative)
                        acceleration = trend.diff().rolling(window=window, min_periods=1).mean()
                        df[f'{metric}_{window}_acceleration'] = acceleration.values
                        
                        # Rate of change percentage
                        pct_change = metric_values.pct_change().rolling(window=window, min_periods=1).mean()
                        df[f'{metric}_{window}_pct_change'] = pct_change.values
                
                # Error escalation rate
                if 'error_count' in available_metrics:
                    error_rolling = df_indexed['error_count'].rolling(window=window, min_periods=1)
                    df[f'error_{window}_escalation'] = error_rolling.apply(
                        lambda x: 1 if len(x) > 1 and x.iloc[-1] > x.iloc[0] * 1.5 else 0
                    ).values
                
            except Exception as e:
                logger.warning(f"Error creating window {window} features: {e}")
        
        return df
    
    def create_early_warning_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create early warning indicators that precede failures"""
        df = df.copy()
        
        # Resource threshold indicators
        df['cpu_high'] = (df['cpu_percent'] > 90).astype(int)
        df['memory_high'] = (df['memory_percent'] > 85).astype(int)
        df['disk_high'] = (df['disk_percent'] > 90).astype(int)
        df['resource_stress'] = (df['cpu_high'] + df['memory_high'] + df['disk_high']).astype(int)
        
        # Degradation indicators
        if 'cpu_percent' in df.columns:
            df['cpu_increasing'] = (df['cpu_percent'].diff() > 0).astype(int)
            df['cpu_rapid_increase'] = (df['cpu_percent'].diff() > 5).astype(int)
        
        if 'memory_percent' in df.columns:
            df['memory_increasing'] = (df['memory_percent'].diff() > 0).astype(int)
            df['memory_rapid_increase'] = (df['memory_percent'].diff() > 3).astype(int)
        
        # Error escalation
        if 'error_count' in df.columns:
            df['error_spike'] = (df['error_count'] > df['error_count'].rolling(60, min_periods=1).mean() * 2).astype(int)
            df['error_escalation'] = (df['error_count'].diff() > 0).astype(int)
        
        # Service degradation
        if 'service_failures' in df.columns:
            df['service_degradation'] = df['service_failures'].rolling(15, min_periods=1).sum()
        
        # Combined early warning score
        warning_features = ['cpu_high', 'memory_high', 'disk_high', 'error_spike', 'service_degradation']
        available_warnings = [f for f in warning_features if f in df.columns]
        if available_warnings:
            df['early_warning_score'] = df[available_warnings].sum(axis=1)
        
        return df
    
    def engineer_features(self, df: pd.DataFrame, target_col: str = 'target') -> Tuple[pd.DataFrame, List[str]]:
        """Perform complete feature engineering with predictive indicators"""
        logger.info("Engineering features with predictive indicators...")
        
        # Create time features
        df = self.create_time_features(df)
        
        # Determine windows
        if self.auto_detect_windows:
            windows = self._auto_detect_windows(df, target_col)
        else:
            windows = ['5min', '15min', '1h', '6h', '24h']
        
        self.optimal_windows = windows
        
        # Create windowed features with trends
        df = self.create_windowed_features(df, windows)
        
        # Create early warning indicators
        df = self.create_early_warning_indicators(df)
        
        # Handle missing values
        df = df.fillna(df.median())
        
        # Remove infinite values
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Get feature names (exclude target, timestamp, and time_until_failure if used for regression)
        exclude_cols = ['timestamp', 'target', 'class', 'time_until_failure', 'is_failure']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        logger.info(f"Created {len(feature_cols)} features including {len([c for c in feature_cols if 'trend' in c or 'warning' in c])} predictive indicators")
        return df, feature_cols


class ModelTrainer:
    """Train XGBoost or GradientBoosting model with dual model support (classification + regression)"""
    
    def __init__(self, use_xgboost: bool = True):
        self.use_xgboost = use_xgboost and XGBOOST_AVAILABLE
        self.model = None  # Classification model
        self.regression_model = None  # Optional regression model for time-to-failure
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              tune_hyperparameters: bool = True, n_iter: int = 20,
              y_train_regression: np.ndarray = None, y_val_regression: np.ndarray = None) -> Tuple[Any, Optional[Any]]:
        """Train classification model with optional regression model for time-to-failure"""
        logger.info("Training classification model...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
        else:
            X_val_scaled = None
        
        # Train classification model
        if self.use_xgboost:
            logger.info("Using XGBoost for classification")
            # Check if both classes are present
            unique_classes = np.unique(y_train)
            if len(unique_classes) < 2:
                logger.warning(f"Only one class ({unique_classes}) present in training data. "
                             f"This may indicate a data issue. Proceeding with training...")
                # If validation set has both classes, we can still train
                if X_val_scaled is not None and y_val is not None and len(np.unique(y_val)) > 1:
                    logger.info("Validation set has both classes, training will proceed.")
            
            if tune_hyperparameters:
                model = self._tune_xgboost(X_train_scaled, y_train, X_val_scaled, y_val, n_iter, is_classification=True)
            else:
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric='logloss',
                    early_stopping_rounds=10 if X_val_scaled is not None else None
                )
                try:
                    if X_val_scaled is not None:
                        model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
                    else:
                        model.fit(X_train_scaled, y_train)
                except ValueError as e:
                    if "Invalid classes" in str(e):
                        logger.error(f"Cannot train XGBoost with only one class. Error: {e}")
                        logger.info("Attempting to use validation set for training...")
                        if X_val_scaled is not None and y_val is not None and len(np.unique(y_val)) > 1:
                            # Combine train and validation for training
                            X_combined = np.vstack([X_train_scaled, X_val_scaled])
                            y_combined = np.concatenate([y_train, y_val])
                            model.fit(X_combined, y_combined)
                        else:
                            raise ValueError("Cannot train model: only one class present in all data")
                    else:
                        raise
        else:
            logger.info("Using GradientBoostingClassifier (XGBoost fallback)")
            if tune_hyperparameters:
                model = self._tune_gradient_boosting(X_train_scaled, y_train, X_val_scaled, y_val, n_iter, is_classification=True)
            else:
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                )
                model.fit(X_train_scaled, y_train)
        
        self.model = model
        
        # Train regression model if targets provided
        regression_model = None
        if y_train_regression is not None:
            logger.info("Training regression model for time-to-failure prediction...")
            # Only train on samples where failure is predicted
            train_mask = y_train == 1
            if train_mask.sum() > 10:  # Need at least 10 samples
                X_train_reg = X_train_scaled[train_mask]
                y_train_reg = y_train_regression[train_mask]
                
                if self.use_xgboost:
                    if tune_hyperparameters:
                        regression_model = self._tune_xgboost(X_train_reg, y_train_reg, None, None, n_iter//2, is_classification=False)
                    else:
                        regression_model = xgb.XGBRegressor(
                            n_estimators=100,
                            max_depth=6,
                            learning_rate=0.1,
                            subsample=0.8,
                            colsample_bytree=0.8,
                            random_state=42,
                            eval_metric='rmse'
                        )
                        regression_model.fit(X_train_reg, y_train_reg)
                else:
                    from sklearn.ensemble import GradientBoostingRegressor
                    if tune_hyperparameters:
                        regression_model = self._tune_gradient_boosting_regression(X_train_reg, y_train_reg, None, None, n_iter//2)
                    else:
                        regression_model = GradientBoostingRegressor(
                            n_estimators=100,
                            max_depth=6,
                            learning_rate=0.1,
                            subsample=0.8,
                            random_state=42
                        )
                        regression_model.fit(X_train_reg, y_train_reg)
                
                self.regression_model = regression_model
                logger.info("Regression model training completed")
            else:
                logger.warning("Not enough positive samples for regression model")
        
        logger.info("Model training completed")
        return model, regression_model
    
    def _tune_xgboost(self, X_train: np.ndarray, y_train: np.ndarray,
                      X_val: np.ndarray, y_val: np.ndarray, n_iter: int, is_classification: bool = True) -> Any:
        """Hyperparameter tuning for XGBoost (classification or regression)"""
        model_type = "classification" if is_classification else "regression"
        logger.info(f"Tuning XGBoost {model_type} hyperparameters ({n_iter} iterations)...")
        
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 4, 5, 6, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.7, 0.8, 0.9],
            'colsample_bytree': [0.6, 0.7, 0.8, 0.9]
        }
        
        if is_classification:
            base_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
            scoring = 'roc_auc'
            
            # Check if both classes are present in training data
            unique_classes = np.unique(y_train)
            if len(unique_classes) < 2:
                logger.warning(f"Only one class ({unique_classes}) present in training data. Skipping hyperparameter tuning.")
                # Use validation set if available, otherwise use a simple split
                if X_val is not None and y_val is not None and len(np.unique(y_val)) > 1:
                    # Combine train and validation, then use stratified split to ensure both classes in training
                    X_combined = np.vstack([X_train, X_val])
                    y_combined = np.concatenate([y_train, y_val])
                    
                    # Use stratified split to ensure both classes are in training fold
                    from sklearn.model_selection import train_test_split
                    X_train_cv, X_val_cv, y_train_cv, y_val_cv = train_test_split(
                        X_combined, y_combined, test_size=len(X_val) / len(X_combined), 
                        random_state=42, stratify=y_combined
                    )
                    
                    # Verify both classes are present, then train directly without CV
                    if len(np.unique(y_train_cv)) < 2:
                        logger.warning("Cannot ensure both classes in training fold. Using default parameters on combined data.")
                        model = xgb.XGBClassifier(
                            n_estimators=100,
                            max_depth=6,
                            learning_rate=0.1,
                            subsample=0.8,
                            colsample_bytree=0.8,
                            random_state=42,
                            eval_metric='logloss'
                        )
                        model.fit(X_combined, y_combined)
                        return model
                    
                    # Train directly on stratified split without CV
                    logger.info("Training on stratified split (both classes present) without hyperparameter tuning.")
                    model = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        eval_metric='logloss'
                    )
                    model.fit(X_train_cv, y_train_cv, eval_set=[(X_val_cv, y_val_cv)], verbose=False)
                    return model
                else:
                    # Cannot use CV with single class, use default parameters
                    logger.warning("Cannot use cross-validation with single class. Using default parameters.")
                    model = xgb.XGBClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        eval_metric='logloss'
                    )
                    if X_val is not None and y_val is not None:
                        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
                    else:
                        model.fit(X_train, y_train)
                    return model
            else:
                # Both classes present, use time series split
                tscv = TimeSeriesSplit(n_splits=3)
                cv = tscv
        else:
            # Regression - use time series split
            tscv = TimeSeriesSplit(n_splits=3)
            cv = tscv
            base_model = xgb.XGBRegressor(random_state=42, eval_metric='rmse')
            scoring = 'neg_mean_absolute_error'
        
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def _tune_gradient_boosting(self, X_train: np.ndarray, y_train: np.ndarray,
                                X_val: np.ndarray, y_val: np.ndarray, n_iter: int, is_classification: bool = True) -> Any:
        """Hyperparameter tuning for GradientBoosting (classification)"""
        logger.info(f"Tuning GradientBoosting classification hyperparameters ({n_iter} iterations)...")
        
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 4, 5, 6, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.7, 0.8, 0.9]
        }
        
        base_model = GradientBoostingClassifier(random_state=42)
        
        # Check if both classes are present in training data
        unique_classes = np.unique(y_train)
        if len(unique_classes) < 2:
            logger.warning(f"Only one class ({unique_classes}) present in training data. Skipping hyperparameter tuning.")
            # Use validation set if available, otherwise use a simple split
            if X_val is not None and y_val is not None and len(np.unique(y_val)) > 1:
                # Combine train and validation, then use stratified split to ensure both classes in training
                X_combined = np.vstack([X_train, X_val])
                y_combined = np.concatenate([y_train, y_val])
                
                # Use stratified split to ensure both classes are in training fold
                from sklearn.model_selection import train_test_split
                X_train_cv, X_val_cv, y_train_cv, y_val_cv = train_test_split(
                    X_combined, y_combined, test_size=len(X_val) / len(X_combined), 
                    random_state=42, stratify=y_combined
                )
                
                # Verify both classes are present, then train directly without CV
                if len(np.unique(y_train_cv)) < 2:
                    logger.warning("Cannot ensure both classes in training fold. Using default parameters on combined data.")
                    model = GradientBoostingClassifier(
                        n_estimators=100,
                        max_depth=6,
                        learning_rate=0.1,
                        subsample=0.8,
                        random_state=42
                    )
                    model.fit(X_combined, y_combined)
                    return model
                
                # Train directly on stratified split without CV
                logger.info("Training on stratified split (both classes present) without hyperparameter tuning.")
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                )
                model.fit(X_train_cv, y_train_cv)
                return model
            else:
                # Cannot use CV with single class, use default parameters
                logger.warning("Cannot use cross-validation with single class. Using default parameters.")
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                )
                model.fit(X_train, y_train)
                return model
        else:
            # Both classes present, use time series split
            tscv = TimeSeriesSplit(n_splits=3)
            cv = tscv
        
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def _tune_gradient_boosting_regression(self, X_train: np.ndarray, y_train: np.ndarray,
                                          X_val: np.ndarray, y_val: np.ndarray, n_iter: int) -> Any:
        """Hyperparameter tuning for GradientBoosting regression"""
        logger.info(f"Tuning GradientBoosting regression hyperparameters ({n_iter} iterations)...")
        
        from sklearn.ensemble import GradientBoostingRegressor
        
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 4, 5, 6, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.7, 0.8, 0.9]
        }
        
        base_model = GradientBoostingRegressor(random_state=42)
        
        tscv = TimeSeriesSplit(n_splits=3)
        
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=tscv,
            scoring='neg_mean_absolute_error',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make classification predictions (failure probability)"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]
    
    def predict_time_to_failure(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predict time until failure (hours) using regression model"""
        if self.regression_model is None:
            return None
        X_scaled = self.scaler.transform(X)
        predictions = self.regression_model.predict(X_scaled)
        return np.clip(predictions, 0, None)  # Ensure non-negative


class MetricsCalculator:
    """Calculate and visualize metrics"""
    
    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.plots_dir = artifact_dir / 'plots'
        self.plots_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          y_pred_proba: np.ndarray, 
                          time_until_failure: Optional[np.ndarray] = None,
                          timestamps: Optional[pd.Series] = None) -> Dict[str, float]:
        """Calculate comprehensive metrics including predictive performance"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.0,
            'pr_auc': average_precision_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.0
        }
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        metrics['tn'], metrics['fp'], metrics['fn'], metrics['tp'] = cm.ravel()
        
        # Predictive performance metrics
        if time_until_failure is not None and timestamps is not None:
            # Early detection rate: % of failures predicted >1 hour before
            failure_indices = np.where(y_true == 1)[0]
            if len(failure_indices) > 0:
                early_detections = 0
                lead_times = []
                
                for idx in failure_indices:
                    # Look back for predictions
                    lookback_window = min(60, idx)  # Up to 60 samples back (1 hour if 1min intervals)
                    if lookback_window > 0:
                        window_start = max(0, idx - lookback_window)
                        window_predictions = y_pred[window_start:idx]
                        if np.any(window_predictions == 1):
                            # Found early prediction
                            early_detections += 1
                            # Calculate lead time
                            first_pred_idx = window_start + np.where(window_predictions == 1)[0][0]
                            if timestamps is not None and len(timestamps) > idx:
                                time_diff = (pd.to_datetime(timestamps.iloc[idx]) - 
                                           pd.to_datetime(timestamps.iloc[first_pred_idx])).total_seconds() / 3600
                                lead_times.append(time_diff)
                
                metrics['early_detection_rate'] = early_detections / len(failure_indices) if len(failure_indices) > 0 else 0.0
                metrics['mean_lead_time_hours'] = np.mean(lead_times) if lead_times else 0.0
                metrics['median_lead_time_hours'] = np.median(lead_times) if lead_times else 0.0
            else:
                metrics['early_detection_rate'] = 0.0
                metrics['mean_lead_time_hours'] = 0.0
                metrics['median_lead_time_hours'] = 0.0
        
        return metrics
    
    def calculate_regression_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics for time-to-failure prediction"""
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # Accuracy within time windows
        within_15min = np.abs(y_true - y_pred) <= 0.25  # 15 minutes = 0.25 hours
        within_1hour = np.abs(y_true - y_pred) <= 1.0
        within_6hours = np.abs(y_true - y_pred) <= 6.0
        
        metrics = {
            'mae_hours': mae,
            'rmse_hours': rmse,
            'accuracy_within_15min': np.mean(within_15min),
            'accuracy_within_1hour': np.mean(within_1hour),
            'accuracy_within_6hours': np.mean(within_6hours)
        }
        
        return metrics
    
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray, save_path: Path):
        """Plot confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
    
    def plot_roc_curve(self, y_true: np.ndarray, y_pred_proba: np.ndarray, save_path: Path):
        """Plot ROC curve"""
        if len(np.unique(y_true)) > 1:
            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
            auc = roc_auc_score(y_true, y_pred_proba)
            
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, label=f'ROC Curve (AUC = {auc:.3f})')
            plt.plot([0, 1], [0, 1], 'k--', label='Random')
            plt.xlabel('False Positive Rate')
            plt.ylabel('True Positive Rate')
            plt.title('ROC Curve')
            plt.legend()
            plt.tight_layout()
            plt.savefig(save_path)
            plt.close()
    
    def plot_feature_importance(self, model: Any, feature_names: List[str], save_path: Path):
        """Plot feature importance"""
        try:
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'get_booster'):
                importances = model.get_booster().get_score(importance_type='gain')
                # Convert to array if needed
                if isinstance(importances, dict):
                    importances = np.array([importances.get(f'f{i}', 0) for i in range(len(feature_names))])
            else:
                logger.warning("Could not extract feature importances")
                return
            
            # Get top 20 features
            indices = np.argsort(importances)[::-1][:20]
            top_features = [feature_names[i] for i in indices]
            top_importances = importances[indices]
            
            plt.figure(figsize=(10, 8))
            plt.barh(range(len(top_features)), top_importances)
            plt.yticks(range(len(top_features)), top_features)
            plt.xlabel('Importance')
            plt.title('Top 20 Feature Importances')
            plt.tight_layout()
            plt.savefig(save_path)
            plt.close()
        except Exception as e:
            logger.warning(f"Error plotting feature importance: {e}")
    
    def plot_prediction_timeline(self, timestamps: pd.Series, y_true: np.ndarray, 
                                 y_pred: np.ndarray, y_pred_proba: np.ndarray, save_path: Path):
        """Plot prediction timeline showing predictions vs actual failures over time"""
        try:
            timestamps_dt = pd.to_datetime(timestamps)
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
            
            # Plot 1: Predictions and actual failures
            ax1.plot(timestamps_dt, y_pred_proba, label='Prediction Probability', alpha=0.7, linewidth=1)
            ax1.scatter(timestamps_dt[y_true == 1], y_pred_proba[y_true == 1], 
                       color='red', marker='x', s=100, label='Actual Failures', zorder=5)
            ax1.axhline(y=0.5, color='orange', linestyle='--', label='Decision Threshold')
            ax1.set_ylabel('Failure Probability')
            ax1.set_title('Prediction Timeline: Predictions vs Actual Failures')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot 2: Binary predictions
            ax2.plot(timestamps_dt, y_pred, label='Predicted (Binary)', alpha=0.7, linewidth=1)
            ax2.plot(timestamps_dt, y_true, label='Actual (Binary)', alpha=0.7, linewidth=1)
            ax2.set_ylabel('Failure (0/1)')
            ax2.set_xlabel('Time')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(save_path, dpi=150)
            plt.close()
        except Exception as e:
            logger.warning(f"Error plotting prediction timeline: {e}")
    
    def plot_lead_time_distribution(self, lead_times: List[float], save_path: Path):
        """Plot histogram of prediction lead times"""
        try:
            if not lead_times:
                logger.warning("No lead times available for plotting")
                return
            
            plt.figure(figsize=(10, 6))
            plt.hist(lead_times, bins=20, edgecolor='black', alpha=0.7)
            plt.xlabel('Lead Time (hours)')
            plt.ylabel('Frequency')
            plt.title('Distribution of Prediction Lead Times')
            plt.axvline(np.mean(lead_times), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(lead_times):.2f} hours')
            plt.axvline(np.median(lead_times), color='green', linestyle='--', 
                       label=f'Median: {np.median(lead_times):.2f} hours')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(save_path, dpi=150)
            plt.close()
        except Exception as e:
            logger.warning(f"Error plotting lead time distribution: {e}")


class SHAPExplainer:
    """Generate SHAP explanations"""
    
    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.shap_dir = artifact_dir / 'shap'
        self.shap_dir.mkdir(parents=True, exist_ok=True)
        self.available = SHAP_AVAILABLE
    
    def explain(self, model: Any, X_test: np.ndarray, feature_names: List[str],
                max_samples: int = 100) -> Optional[np.ndarray]:
        """Generate SHAP explanations"""
        if not self.available:
            logger.warning("SHAP not available, skipping explanations")
            return None
        
        logger.info("Generating SHAP explanations...")
        
        try:
            # Sample for faster computation
            if len(X_test) > max_samples:
                sample_indices = np.random.choice(len(X_test), max_samples, replace=False)
                X_sample = X_test[sample_indices]
            else:
                X_sample = X_test
                sample_indices = np.arange(len(X_test))
            
            # Create explainer
            if self._is_xgboost(model):
                explainer = shap.TreeExplainer(model)
            else:
                explainer = shap.Explainer(model, X_sample)
            
            shap_values = explainer.shap_values(X_sample)
            
            # Handle different return formats
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # For binary classification, use positive class
            
            # Save SHAP values
            np.save(self.shap_dir / 'shap_values.npy', shap_values)
            
            # Create plots
            self._create_shap_plots(shap_values, X_sample, feature_names, model)
            
            logger.info("SHAP explanations generated")
            return shap_values
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanations: {e}")
            return None
    
    def _is_xgboost(self, model: Any) -> bool:
        """Check if model is XGBoost"""
        return hasattr(model, 'get_booster') or 'xgboost' in str(type(model)).lower()
    
    def _create_shap_plots(self, shap_values: np.ndarray, X: np.ndarray,
                          feature_names: List[str], model: Any):
        """Create SHAP visualization plots"""
        try:
            # Summary plot
            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values, X, feature_names=feature_names, show=False, max_display=20)
            plt.tight_layout()
            plt.savefig(self.shap_dir / 'summary_plot.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            # Bar plot
            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values, X, feature_names=feature_names, plot_type='bar', show=False, max_display=20)
            plt.tight_layout()
            plt.savefig(self.shap_dir / 'bar_plot.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            # Waterfall plot for first sample
            if len(shap_values.shape) == 2 and shap_values.shape[0] > 0:
                try:
                    shap.waterfall_plot(
                        shap.Explanation(
                            values=shap_values[0],
                            base_values=shap_values[0].sum() if hasattr(model, 'predict_proba') else 0,
                            data=X[0],
                            feature_names=feature_names[:len(shap_values[0])]
                        ),
                        show=False
                    )
                    plt.tight_layout()
                    plt.savefig(self.shap_dir / 'waterfall_plot.png', dpi=150, bbox_inches='tight')
                    plt.close()
                except Exception as e:
                    logger.debug(f"Could not create waterfall plot: {e}")
                    
        except Exception as e:
            logger.warning(f"Error creating SHAP plots: {e}")


class ArtifactManager:
    """Manage model artifacts and versioning"""
    
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).parent / 'artifacts'
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create version directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.version_dir = self.base_dir / f'v{timestamp}'
        self.version_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Artifact directory: {self.version_dir}")
    
    def save_model(self, model: Any, scaler: StandardScaler, feature_names: List[str],
                   metrics: Dict[str, Any], config: Dict[str, Any],
                   regression_model: Optional[Any] = None, prediction_thresholds: Optional[Dict[str, float]] = None):
        """Save all model artifacts including regression model and thresholds"""
        # Save classification model
        if hasattr(model, 'save_model'):
            # XGBoost
            model_path = self.version_dir / 'model.json'
            model.save_model(str(model_path))
        else:
            # Scikit-learn
            model_path = self.version_dir / 'model.pkl'
            joblib.dump(model, model_path)
        
        # Save regression model if available
        if regression_model is not None:
            if hasattr(regression_model, 'save_model'):
                reg_model_path = self.version_dir / 'regression_model.json'
                regression_model.save_model(str(reg_model_path))
            else:
                reg_model_path = self.version_dir / 'regression_model.pkl'
                joblib.dump(regression_model, reg_model_path)
            logger.info(f"Regression model saved to {reg_model_path}")
        
        # Save scaler
        scaler_path = self.version_dir / 'scaler.pkl'
        joblib.dump(scaler, scaler_path)
        
        # Save feature names
        feature_path = self.version_dir / 'feature_names.json'
        with open(feature_path, 'w') as f:
            json.dump(feature_names, f, indent=2)
        
        # Save metrics (convert numpy types to native Python types)
        def convert_numpy_types(obj):
            """Recursively convert numpy types to native Python types for JSON serialization"""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_numpy_types(item) for item in obj)
            else:
                return obj
        
        metrics_serializable = convert_numpy_types(metrics)
        metrics_path = self.version_dir / 'metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics_serializable, f, indent=2)
        
        # Save prediction thresholds
        if prediction_thresholds is None:
            # Calculate optimal threshold from metrics if available
            prediction_thresholds = {
                'early_warning': 0.3,  # Low threshold for early warnings
                'high_risk': 0.7,  # High threshold for critical alerts
                'decision': 0.5  # Standard decision threshold
            }
        
        thresholds_path = self.version_dir / 'prediction_thresholds.json'
        with open(thresholds_path, 'w') as f:
            json.dump(prediction_thresholds, f, indent=2)
        
        # Save config (convert numpy types to native Python types)
        config_serializable = convert_numpy_types(config)
        config_path = self.version_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config_serializable, f, indent=2)
        
        logger.info(f"Model artifacts saved to {self.version_dir}")
    
    def create_latest_symlink(self):
        """Create symlink to latest version"""
        latest_dir = self.base_dir / 'latest'
        if latest_dir.exists():
            if latest_dir.is_symlink():
                latest_dir.unlink()
            elif latest_dir.is_file():
                # Handle case where 'latest' is a text file (git may track it as a file)
                logger.warning(f"'{latest_dir}' exists as a file, removing it to create symlink")
                latest_dir.unlink()
            else:
                import shutil
                shutil.rmtree(latest_dir)
        
        try:
            latest_dir.symlink_to(self.version_dir.name)
            logger.info(f"Created symlink: {latest_dir} -> {self.version_dir.name}")
        except Exception as e:
            # On Windows or if symlink fails, copy instead
            logger.warning(f"Could not create symlink, copying instead: {e}")
            import shutil
            if latest_dir.exists():
                if latest_dir.is_file():
                    latest_dir.unlink()
                else:
                    shutil.rmtree(latest_dir)
            shutil.copytree(self.version_dir, latest_dir)
    
    def get_version_dir(self) -> Path:
        """Get version directory path"""
        return self.version_dir


def time_based_split(df: pd.DataFrame, test_size: float = 0.2,
                     target_col: str = 'target') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Time-based train/test split"""
    df = df.sort_values('timestamp')
    split_idx = int(len(df) * (1 - test_size))
    
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    logger.info(f"Train set: {len(train_df)} samples ({train_df[target_col].sum()} positive)")
    logger.info(f"Test set: {len(test_df)} samples ({test_df[target_col].sum()} positive)")
    
    return train_df, test_df


def create_fastapi_loader(artifact_dir: Path, version_dir: Path):
    """Create FastAPI-compatible model loader for predictive maintenance"""
    loader_code = '''"""
FastAPI Model Loader for Predictive Maintenance System Anomaly Detection

This module provides real-time prediction functions for dashboard integration:
- predict_anomaly(): Real-time anomaly detection
- predict_failure_risk(): Risk score (0-1) for failure probability
- predict_time_to_failure(): Estimated hours until failure
- get_early_warnings(): List of early warning indicators
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import joblib

# Try to import XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "model.json" if XGBOOST_AVAILABLE else MODEL_DIR / "model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
FEATURE_NAMES_PATH = MODEL_DIR / "feature_names.json"

# Load artifacts
model = None
scaler = None
feature_names = []

try:
    # Load feature names first if available
    if FEATURE_NAMES_PATH.exists():
        with open(FEATURE_NAMES_PATH, 'r') as f:
            feature_names = json.load(f)
    
    if XGBOOST_AVAILABLE and (MODEL_DIR / "model.json").exists():
        model = xgb.Booster()
        model.load_model(str(MODEL_DIR / "model.json"))
        # Wrap in XGBClassifier for predict_proba
        from xgboost import XGBClassifier
        wrapper = XGBClassifier()
        wrapper._Booster = model
        wrapper.classes_ = np.array([0, 1])
        wrapper.n_features_in_ = len(feature_names) if feature_names else 27
        model = wrapper
    elif (MODEL_DIR / "model.pkl").exists():
        model = joblib.load(MODEL_DIR / "model.pkl")
    
    if SCALER_PATH.exists():
        scaler = joblib.load(SCALER_PATH)
    
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {{e}}")
    model = None

# Load regression model if available
regression_model = None
THRESHOLDS_PATH = MODEL_DIR / "prediction_thresholds.json"
prediction_thresholds = {
    'early_warning': 0.3,
    'high_risk': 0.7,
    'decision': 0.5
}

try:
    if THRESHOLDS_PATH.exists():
        with open(THRESHOLDS_PATH, 'r') as f:
            prediction_thresholds = json.load(f)
    
    # Load regression model
    if XGBOOST_AVAILABLE and (MODEL_DIR / "regression_model.json").exists():
        regression_model = xgb.Booster()
        regression_model.load_model(str(MODEL_DIR / "regression_model.json"))
        from xgboost import XGBRegressor
        wrapper = XGBRegressor()
        wrapper._Booster = regression_model
        wrapper.n_features_in_ = len(feature_names) if feature_names else len(feature_names)
        regression_model = wrapper
    elif (MODEL_DIR / "regression_model.pkl").exists():
        regression_model = joblib.load(MODEL_DIR / "regression_model.pkl")
except Exception as e:
    logger.warning(f"Regression model not available: {e}")

def extract_features_from_metrics(metrics: Dict[str, Any], feature_names: List[str]) -> np.ndarray:
    """Extract features from system metrics dictionary"""
    try:
        features = []
        for feat_name in feature_names:
            # Try different key formats
            value = metrics.get(feat_name, 
                              metrics.get(feat_name.replace('_', ' '), 
                                        metrics.get(feat_name.upper(), 0.0)))
            features.append(float(value) if value is not None else 0.0)
        return np.array(features).reshape(1, -1)
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return np.zeros((1, len(feature_names)))

def predict_anomaly(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Real-time anomaly detection"""
    from datetime import datetime
    try:
        if model is None or scaler is None:
            return {'error': 'Model not loaded', 'is_anomaly': False}
        
        features = extract_features_from_metrics(metrics, feature_names)
        features_scaled = scaler.transform(features)
        prediction_proba = model.predict_proba(features_scaled)[0, 1]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'is_anomaly': bool(prediction_proba > prediction_thresholds['decision']),
            'anomaly_score': float(prediction_proba),
            'risk_level': 'High' if prediction_proba > prediction_thresholds['high_risk'] 
                         else 'Medium' if prediction_proba > prediction_thresholds['decision'] 
                         else 'Low'
        }
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {'error': str(e), 'is_anomaly': False}

def predict_failure_risk(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Get failure risk score (0-1) for failure probability"""
    from datetime import datetime
    try:
        if model is None or scaler is None:
            return {'error': 'Model not loaded', 'risk_score': 0.0}
        
        features = extract_features_from_metrics(metrics, feature_names)
        features_scaled = scaler.transform(features)
        risk_score = float(model.predict_proba(features_scaled)[0, 1])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'risk_score': risk_score,
            'risk_percentage': risk_score * 100,
            'has_early_warning': risk_score > prediction_thresholds['early_warning'],
            'is_high_risk': risk_score > prediction_thresholds['high_risk']
        }
    except Exception as e:
        logger.error(f"Risk prediction error: {e}")
        return {'error': str(e), 'risk_score': 0.0}

def predict_time_to_failure(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Predict estimated hours until failure"""
    from datetime import datetime, timedelta
    try:
        if model is None or scaler is None:
            return {'error': 'Model not loaded', 'hours_until_failure': None}
        
        features = extract_features_from_metrics(metrics, feature_names)
        features_scaled = scaler.transform(features)
        risk_score = float(model.predict_proba(features_scaled)[0, 1])
        
        if risk_score < prediction_thresholds['decision']:
            return {
                'timestamp': datetime.now().isoformat(),
                'hours_until_failure': None,
                'message': 'No failure predicted in near future'
            }
        
        if regression_model is not None:
            hours = float(regression_model.predict(features_scaled)[0])
            hours = max(0, hours)  # Ensure non-negative
            predicted_time = datetime.now() + timedelta(hours=hours)
            return {
                'timestamp': datetime.now().isoformat(),
                'hours_until_failure': hours,
                'predicted_failure_time': predicted_time.isoformat(),
                'confidence': 'High' if risk_score > prediction_thresholds['high_risk'] else 'Medium'
            }
        else:
            # Fallback: estimate based on risk score
            estimated_hours = 24 * (1 - risk_score)  # Inverse relationship
            predicted_time = datetime.now() + timedelta(hours=estimated_hours)
            return {
                'timestamp': datetime.now().isoformat(),
                'hours_until_failure': estimated_hours,
                'predicted_failure_time': predicted_time.isoformat(),
                'confidence': 'Low (regression model not available)',
                'note': 'Estimate based on risk score only'
            }
    except Exception as e:
        logger.error(f"Time-to-failure prediction error: {e}")
        return {'error': str(e), 'hours_until_failure': None}

def get_early_warnings(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Get list of active early warning indicators"""
    from datetime import datetime
    warnings = []
    
    # Resource warnings
    if metrics.get('cpu_percent', 0) > 90:
        warnings.append({'type': 'cpu_high', 'severity': 'high', 'message': f"CPU usage at {metrics.get('cpu_percent', 0):.1f}%"})
    elif metrics.get('cpu_percent', 0) > 80:
        warnings.append({'type': 'cpu_elevated', 'severity': 'medium', 'message': f"CPU usage elevated: {metrics.get('cpu_percent', 0):.1f}%"})
    
    if metrics.get('memory_percent', 0) > 85:
        warnings.append({'type': 'memory_high', 'severity': 'high', 'message': f"Memory usage at {metrics.get('memory_percent', 0):.1f}%"})
    
    if metrics.get('disk_percent', 0) > 90:
        warnings.append({'type': 'disk_high', 'severity': 'high', 'message': f"Disk usage at {metrics.get('disk_percent', 0):.1f}%"})
    
    # Error rate warnings
    if metrics.get('error_count', 0) > 10:
        warnings.append({'type': 'error_spike', 'severity': 'high', 'message': f"High error count: {metrics.get('error_count', 0)}"})
    
    # Get risk score
    risk_result = predict_failure_risk(metrics)
    if risk_result.get('has_early_warning', False):
        warnings.append({
            'type': 'ml_prediction',
            'severity': 'high' if risk_result.get('is_high_risk') else 'medium',
            'message': f"ML model predicts failure risk: {risk_result.get('risk_percentage', 0):.1f}%"
        })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'warning_count': len(warnings),
        'warnings': warnings,
        'has_warnings': len(warnings) > 0
    }
'''
    
    loader_path = artifact_dir / 'latest' / 'model_loader.py'
    loader_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(loader_path, 'w') as f:
        f.write(loader_code)
    
    logger.info(f"FastAPI loader created at {loader_path}")


def main():
    """Main training pipeline for predictive maintenance"""
    parser = argparse.ArgumentParser(description='Train XGBoost model for predictive maintenance and system anomaly detection')
    parser.add_argument('--data-path', type=str, default=None, help='Path to training data CSV')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size (default: 0.2)')
    parser.add_argument('--n-iter', type=int, default=20, help='Hyperparameter tuning iterations (default: 20)')
    parser.add_argument('--no-tuning', action='store_true', help='Skip hyperparameter tuning')
    parser.add_argument('--no-shap', action='store_true', help='Skip SHAP explanations')
    parser.add_argument('--target-col', type=str, default='target', help='Target column name (default: target)')
    parser.add_argument('--artifacts-dir', type=str, default=None, help='Artifacts directory')
    parser.add_argument('--prediction-horizon', type=int, nargs='+', default=[1, 6, 24], 
                       help='Hours ahead to predict (default: 1 6 24)')
    parser.add_argument('--enable-regression', action='store_true', 
                       help='Also train time-to-failure regression model')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("XGBoost Training Pipeline for Predictive Maintenance & Proactive Intelligence")
    logger.info("=" * 80)
    
    # Initialize components
    data_loader = DataLoader(data_path=args.data_path, prediction_horizon=args.prediction_horizon)
    feature_engineer = FeatureEngineer(auto_detect_windows=True)
    model_trainer = ModelTrainer(use_xgboost=XGBOOST_AVAILABLE)
    
    # Load and prepare data
    logger.info("Step 1: Loading data with predictive labeling...")
    df = data_loader.load_data()
    
    # Determine target column
    target_col = args.target_col
    if target_col not in df.columns and 'class' in df.columns:
        target_col = 'class'
        logger.info(f"Using 'class' as target column")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Available columns: {df.columns.tolist()}")
    
    # Feature engineering
    logger.info("Step 2: Feature engineering with predictive indicators...")
    df, feature_cols = feature_engineer.engineer_features(df, target_col=target_col)
    
    # Time-based split
    logger.info("Step 3: Time-based train/test split...")
    train_df, test_df = time_based_split(df, test_size=args.test_size, target_col=target_col)
    
    # Prepare features and targets
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    # Prepare regression targets if enabled
    y_train_regression = None
    y_test_regression = None
    if args.enable_regression and 'time_until_failure' in train_df.columns:
        y_train_regression = train_df['time_until_failure'].values
        y_test_regression = test_df['time_until_failure'].values
        logger.info("Regression targets prepared for time-to-failure prediction")
    
    model_trainer.feature_names = feature_cols
    
    # Train model
    logger.info("Step 4: Training classification model...")
    model, regression_model = model_trainer.train(
        X_train, y_train, X_test, y_test,
        tune_hyperparameters=not args.no_tuning,
        n_iter=args.n_iter,
        y_train_regression=y_train_regression,
        y_val_regression=y_test_regression
    )
    
    # Make predictions
    logger.info("Step 5: Making predictions...")
    y_pred_proba = model_trainer.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Time-to-failure predictions if regression model available
    y_pred_time = None
    if regression_model is not None:
        y_pred_time = model_trainer.predict_time_to_failure(X_test)
        logger.info("Time-to-failure predictions generated")
    
    # Calculate metrics
    logger.info("Step 6: Calculating metrics including predictive performance...")
    artifact_manager = ArtifactManager(base_dir=Path(args.artifacts_dir) if args.artifacts_dir else None)
    metrics_calc = MetricsCalculator(artifact_manager.get_version_dir())
    
    # Calculate classification metrics with predictive performance
    metrics = metrics_calc.calculate_metrics(
        y_test, y_pred, y_pred_proba,
        time_until_failure=test_df['time_until_failure'].values if 'time_until_failure' in test_df.columns else None,
        timestamps=test_df['timestamp'] if 'timestamp' in test_df.columns else None
    )
    
    # Calculate regression metrics if available
    regression_metrics = {}
    if y_pred_time is not None and y_test_regression is not None:
        regression_metrics = metrics_calc.calculate_regression_metrics(y_test_regression, y_pred_time)
        metrics.update(regression_metrics)
    
    # Create visualizations
    logger.info("Step 7: Creating visualizations...")
    plots_dir = artifact_manager.get_version_dir() / 'plots'
    metrics_calc.plot_confusion_matrix(y_test, y_pred, plots_dir / 'confusion_matrix.png')
    metrics_calc.plot_roc_curve(y_test, y_pred_proba, plots_dir / 'roc_curve.png')
    metrics_calc.plot_feature_importance(model, feature_cols, plots_dir / 'feature_importance.png')
    
    # Prediction timeline plot
    if 'timestamp' in test_df.columns:
        metrics_calc.plot_prediction_timeline(
            test_df['timestamp'], y_test, y_pred, y_pred_proba,
            plots_dir / 'prediction_timeline.png'
        )
    
    # SHAP explanations
    if not args.no_shap and SHAP_AVAILABLE:
        logger.info("Step 8: Generating SHAP explanations...")
        shap_explainer = SHAPExplainer(artifact_manager.get_version_dir())
        shap_values = shap_explainer.explain(model, X_test, feature_cols)
    else:
        logger.info("Step 8: Skipping SHAP explanations")
    
    # Calculate optimal thresholds
    from sklearn.metrics import roc_curve
    if len(np.unique(y_test)) > 1:
        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
        # Find threshold that maximizes TPR - FPR
        optimal_idx = np.argmax(tpr - fpr)
        optimal_threshold = thresholds[optimal_idx]
    else:
        optimal_threshold = 0.5
    
    prediction_thresholds = {
        'early_warning': 0.3,
        'high_risk': 0.7,
        'decision': float(optimal_threshold)
    }
    
    # Save artifacts
    logger.info("Step 9: Saving artifacts...")
    config = {
        'model_type': 'xgboost' if XGBOOST_AVAILABLE else 'gradient_boosting',
        'has_regression_model': regression_model is not None,
        'feature_count': len(feature_cols),
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'optimal_windows': feature_engineer.optimal_windows,
        'hyperparameter_tuning': not args.no_tuning,
        'prediction_horizon_hours': args.prediction_horizon,
        'timestamp': datetime.now().isoformat()
    }
    
    artifact_manager.save_model(
        model, model_trainer.scaler, feature_cols, metrics, config,
        regression_model=regression_model,
        prediction_thresholds=prediction_thresholds
    )
    
    # Create latest symlink
    artifact_manager.create_latest_symlink()
    
    # Create FastAPI loader
    logger.info("Step 10: Creating FastAPI loader for dashboard integration...")
    create_fastapi_loader(artifact_manager.base_dir, artifact_manager.get_version_dir())
    
    # Print summary
    logger.info("=" * 80)
    logger.info("Training Summary - Predictive Maintenance")
    logger.info("=" * 80)
    logger.info(f"Model Type: {config['model_type']}")
    logger.info(f"Regression Model: {'Yes' if regression_model is not None else 'No'}")
    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Train Samples: {len(train_df)}")
    logger.info(f"Test Samples: {len(test_df)}")
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
    logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"PR-AUC: {metrics['pr_auc']:.4f}")
    if 'early_detection_rate' in metrics:
        logger.info(f"Early Detection Rate: {metrics['early_detection_rate']:.2%}")
        logger.info(f"Mean Lead Time: {metrics.get('mean_lead_time_hours', 0):.2f} hours")
    if regression_metrics:
        logger.info(f"Time-to-Failure MAE: {regression_metrics.get('mae_hours', 0):.2f} hours")
        logger.info(f"Accuracy within 1 hour: {regression_metrics.get('accuracy_within_1hour', 0):.2%}")
    logger.info(f"Artifacts saved to: {artifact_manager.get_version_dir()}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

