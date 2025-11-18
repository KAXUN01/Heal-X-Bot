#!/usr/bin/env python3
"""
Advanced XGBoost Training Pipeline for DDoS Detection

This script trains a predictive model using XGBoost (with GradientBoosting fallback)
for DDoS detection with comprehensive feature engineering, evaluation, and artifact management.
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

# Feature names from existing detector
FEATURE_NAMES = [
    "Protocol", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean", "Flow IAT Mean",
    "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Mean",
    "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Active Mean",
    "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std",
    "Idle Max", "Idle Min"
]


class DataLoader:
    """Load data from logs or generate synthetic data"""
    
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.project_root = Path(__file__).parent.parent
        
    def load_from_logs(self) -> Optional[pd.DataFrame]:
        """Load data from system logs"""
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
        
        logger.info(f"Loaded {len(df)} records from logs")
        return df
    
    def _extract_features_from_log(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from log entry"""
        # Extract timestamp
        timestamp = entry.get('timestamp', entry.get('@timestamp', datetime.now().isoformat()))
        
        # Extract metrics if available
        metrics = entry.get('metrics', {})
        message = entry.get('message', '')
        
        # Try to extract numeric values from message or metrics
        record = {'timestamp': timestamp}
        
        # Map log data to features (simplified - would need domain-specific parsing)
        for i, feature_name in enumerate(FEATURE_NAMES):
            key = feature_name.lower().replace(' ', '_')
            value = metrics.get(key, 0.0)
            if value == 0.0:
                # Try to extract from message or use random for demo
                value = np.random.uniform(0, 1000) if 'ddos' in message.lower() else np.random.uniform(0, 100)
            record[feature_name] = float(value)
        
        # Generate target based on log level or keywords
        target = 1 if (
            entry.get('level', '').upper() in ['ERROR', 'CRITICAL', 'ALERT'] or
            'ddos' in message.lower() or
            'attack' in message.lower()
        ) else 0
        
        record['target'] = target
        return record
    
    def generate_synthetic_data(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic DDoS detection data"""
        logger.info(f"Generating {n_samples} synthetic samples")
        
        np.random.seed(42)
        data = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(n_samples):
            # Generate timestamp
            timestamp = base_time + timedelta(seconds=i * 60)  # 1 minute intervals
            
            # Determine if this is a DDoS attack (20% of samples)
            is_ddos = np.random.random() < 0.2
            
            # Generate features based on attack status
            if is_ddos:
                # DDoS attack characteristics
                protocol = np.random.choice([6, 17])  # TCP or UDP
                flow_duration = np.random.uniform(100, 5000)
                total_fwd_packets = np.random.uniform(1000, 10000)
                total_backward_packets = np.random.uniform(10, 100)
                fwd_packet_length_mean = np.random.uniform(50, 1500)
                bwd_packet_length_mean = np.random.uniform(0, 100)
                flow_iat_mean = np.random.uniform(0.1, 10)
                flow_iat_std = np.random.uniform(0.1, 5)
                flow_iat_max = np.random.uniform(1, 50)
                flow_iat_min = np.random.uniform(0.01, 1)
            else:
                # Normal traffic characteristics
                protocol = np.random.choice([6, 17, 1])  # TCP, UDP, or ICMP
                flow_duration = np.random.uniform(1000, 60000)
                total_fwd_packets = np.random.uniform(10, 500)
                total_backward_packets = np.random.uniform(5, 200)
                fwd_packet_length_mean = np.random.uniform(500, 1500)
                bwd_packet_length_mean = np.random.uniform(500, 1500)
                flow_iat_mean = np.random.uniform(10, 1000)
                flow_iat_std = np.random.uniform(5, 100)
                flow_iat_max = np.random.uniform(100, 5000)
                flow_iat_min = np.random.uniform(1, 100)
            
            # Generate remaining features
            record = {
                'timestamp': timestamp.isoformat(),
                'Protocol': protocol,
                'Flow Duration': flow_duration,
                'Total Fwd Packets': total_fwd_packets,
                'Total Backward Packets': total_backward_packets,
                'Fwd Packet Length Mean': fwd_packet_length_mean,
                'Bwd Packet Length Mean': bwd_packet_length_mean,
                'Flow IAT Mean': flow_iat_mean,
                'Flow IAT Std': flow_iat_std,
                'Flow IAT Max': flow_iat_max,
                'Flow IAT Min': flow_iat_min,
                'Fwd IAT Mean': np.random.uniform(1, 1000),
                'Fwd IAT Std': np.random.uniform(0.1, 100),
                'Fwd IAT Max': np.random.uniform(10, 5000),
                'Fwd IAT Min': np.random.uniform(0.1, 100),
                'Bwd IAT Mean': np.random.uniform(1, 1000),
                'Bwd IAT Std': np.random.uniform(0.1, 100),
                'Bwd IAT Max': np.random.uniform(10, 5000),
                'Bwd IAT Min': np.random.uniform(0.1, 100),
                'Active Mean': np.random.uniform(0, 10000),
                'Active Std': np.random.uniform(0, 1000),
                'Active Max': np.random.uniform(0, 50000),
                'Active Min': np.random.uniform(0, 100),
                'Idle Mean': np.random.uniform(0, 10000),
                'Idle Std': np.random.uniform(0, 1000),
                'Idle Max': np.random.uniform(0, 50000),
                'Idle Min': np.random.uniform(0, 100),
                'target': 1 if is_ddos else 0
            }
            
            data.append(record)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated synthetic dataset with {len(df)} samples, {df['target'].sum()} DDoS attacks")
        return df
    
    def load_data(self) -> pd.DataFrame:
        """Load data from logs or generate synthetic"""
        if self.data_path and Path(self.data_path).exists():
            logger.info(f"Loading data from {self.data_path}")
            df = pd.read_csv(self.data_path)
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.date_range(start=datetime.now() - timedelta(days=len(df)), periods=len(df), freq='1min')
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
        """Create temporal features"""
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
        
        return df
    
    def create_windowed_features(self, df: pd.DataFrame, windows: List[str]) -> pd.DataFrame:
        """Create rolling window features"""
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Set timestamp as index for rolling operations
        df_indexed = df.set_index('timestamp')
        
        # Get numeric columns (excluding target and timestamp)
        numeric_cols = df_indexed.select_dtypes(include=[np.number]).columns.tolist()
        if 'target' in numeric_cols:
            numeric_cols.remove('target')
        if 'class' in numeric_cols:
            numeric_cols.remove('class')
        
        for window in windows:
            try:
                # Use time-based rolling window
                rolling = df_indexed[numeric_cols].rolling(window=window, min_periods=1)
                
                # Rolling statistics - aggregate across all numeric columns
                rolling_mean = rolling.mean().mean(axis=1)
                rolling_std = rolling.std().mean(axis=1)
                rolling_min = rolling.min().min(axis=1)
                rolling_max = rolling.max().max(axis=1)
                rolling_count = rolling.count().sum(axis=1)
                
                # Add to dataframe
                df[f'{window}_mean'] = rolling_mean.values
                df[f'{window}_std'] = rolling_std.values
                df[f'{window}_min'] = rolling_min.values
                df[f'{window}_max'] = rolling_max.values
                df[f'{window}_count'] = rolling_count.values
            except Exception as e:
                logger.warning(f"Error creating window {window} features: {e}")
        
        return df
    
    def engineer_features(self, df: pd.DataFrame, target_col: str = 'target') -> Tuple[pd.DataFrame, List[str]]:
        """Perform complete feature engineering"""
        logger.info("Engineering features...")
        
        # Create time features
        df = self.create_time_features(df)
        
        # Determine windows
        if self.auto_detect_windows:
            windows = self._auto_detect_windows(df, target_col)
        else:
            windows = ['5min', '15min', '1h']
        
        self.optimal_windows = windows
        
        # Create windowed features
        df = self.create_windowed_features(df, windows)
        
        # Handle missing values
        df = df.fillna(df.median())
        
        # Remove infinite values
        df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Get feature names (exclude target and timestamp)
        feature_cols = [col for col in df.columns if col not in ['timestamp', 'target', 'class']]
        self.feature_names = feature_cols
        
        logger.info(f"Created {len(feature_cols)} features")
        return df, feature_cols


class ModelTrainer:
    """Train XGBoost or GradientBoosting model"""
    
    def __init__(self, use_xgboost: bool = True):
        self.use_xgboost = use_xgboost and XGBOOST_AVAILABLE
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              tune_hyperparameters: bool = True, n_iter: int = 20) -> Any:
        """Train model with optional hyperparameter tuning"""
        logger.info("Training model...")
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
        else:
            X_val_scaled = None
        
        if self.use_xgboost:
            logger.info("Using XGBoost")
            if tune_hyperparameters:
                model = self._tune_xgboost(X_train_scaled, y_train, X_val_scaled, y_val, n_iter)
            else:
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric='logloss'
                )
                if X_val_scaled is not None:
                    model.fit(X_train_scaled, y_train, eval_set=[(X_val_scaled, y_val)], verbose=False)
                else:
                    model.fit(X_train_scaled, y_train)
        else:
            logger.info("Using GradientBoostingClassifier (XGBoost fallback)")
            if tune_hyperparameters:
                model = self._tune_gradient_boosting(X_train_scaled, y_train, X_val_scaled, y_val, n_iter)
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
        logger.info("Model training completed")
        return model
    
    def _tune_xgboost(self, X_train: np.ndarray, y_train: np.ndarray,
                      X_val: np.ndarray, y_val: np.ndarray, n_iter: int) -> Any:
        """Hyperparameter tuning for XGBoost"""
        logger.info(f"Tuning XGBoost hyperparameters ({n_iter} iterations)...")
        
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 4, 5, 6, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.7, 0.8, 0.9],
            'colsample_bytree': [0.6, 0.7, 0.8, 0.9]
        }
        
        base_model = xgb.XGBClassifier(random_state=42, eval_metric='logloss')
        
        # Use time series split for cross-validation
        tscv = TimeSeriesSplit(n_splits=3)
        
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=tscv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def _tune_gradient_boosting(self, X_train: np.ndarray, y_train: np.ndarray,
                                X_val: np.ndarray, y_val: np.ndarray, n_iter: int) -> Any:
        """Hyperparameter tuning for GradientBoosting"""
        logger.info(f"Tuning GradientBoosting hyperparameters ({n_iter} iterations)...")
        
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 4, 5, 6, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'subsample': [0.6, 0.7, 0.8, 0.9]
        }
        
        base_model = GradientBoostingClassifier(random_state=42)
        
        tscv = TimeSeriesSplit(n_splits=3)
        
        random_search = RandomizedSearchCV(
            base_model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=tscv,
            scoring='roc_auc',
            n_jobs=-1,
            random_state=42,
            verbose=1
        )
        
        random_search.fit(X_train, y_train)
        logger.info(f"Best parameters: {random_search.best_params_}")
        logger.info(f"Best CV score: {random_search.best_score_:.4f}")
        
        return random_search.best_estimator_
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]


class MetricsCalculator:
    """Calculate and visualize metrics"""
    
    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.plots_dir = artifact_dir / 'plots'
        self.plots_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                          y_pred_proba: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive metrics"""
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
                   metrics: Dict[str, Any], config: Dict[str, Any]):
        """Save all model artifacts"""
        # Save model
        if hasattr(model, 'save_model'):
            # XGBoost
            model_path = self.version_dir / 'model.json'
            model.save_model(str(model_path))
        else:
            # Scikit-learn
            model_path = self.version_dir / 'model.pkl'
            joblib.dump(model, model_path)
        
        # Save scaler
        scaler_path = self.version_dir / 'scaler.pkl'
        joblib.dump(scaler, scaler_path)
        
        # Save feature names
        feature_path = self.version_dir / 'feature_names.json'
        with open(feature_path, 'w') as f:
            json.dump(feature_names, f, indent=2)
        
        # Save metrics
        metrics_path = self.version_dir / 'metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save config
        config_path = self.version_dir / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Model artifacts saved to {self.version_dir}")
    
    def create_latest_symlink(self):
        """Create symlink to latest version"""
        latest_dir = self.base_dir / 'latest'
        if latest_dir.exists():
            if latest_dir.is_symlink():
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
    """Create FastAPI-compatible model loader"""
    loader_code = f'''"""
FastAPI Model Loader for XGBoost DDoS Detection Model

This module provides a predict_ddos function compatible with the existing ddos_detector.py interface.
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

# Original feature names from ddos_detector.py
ORIGINAL_FEATURE_NAMES = [
    "Protocol", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean", "Flow IAT Mean",
    "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Mean",
    "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Active Mean",
    "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std",
    "Idle Max", "Idle Min"
]

def extract_features_from_alert(alert_json: Dict[str, Any]) -> List[float]:
    """Extract features from alert JSON (compatible with ddos_detector.py)"""
    try:
        metrics = alert_json.get('metrics', {{}})
        features = []
        
        # Map incoming metrics to feature list
        for feature in ORIGINAL_FEATURE_NAMES:
            key = feature.lower().replace(' ', '_')
            value = metrics.get(key, 0.0)
            features.append(float(value))
        
        return features
    except Exception as e:
        logger.error(f"Error extracting features: {{e}}")
        return [0.0] * len(ORIGINAL_FEATURE_NAMES)

def predict_ddos(alert_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict DDoS probability (compatible with ddos_detector.py interface)
    
    Returns the same format as the original predict_ddos function.
    """
    from datetime import datetime
    
    try:
        if model is None or scaler is None:
            raise ValueError("Model or scaler not loaded")
        
        # Extract features
        features = extract_features_from_alert(alert_json)
        features_array = np.array(features).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        
        # Make prediction
        prediction_proba = model.predict_proba(features_scaled)[0]
        prediction = prediction_proba[1] if len(prediction_proba) > 1 else prediction_proba[0]
        confidence = abs(prediction - 0.5) * 2  # Scale confidence 0-1
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return {{
            'timestamp': timestamp,
            'prediction': float(prediction),
            'is_ddos': bool(prediction > 0.5),
            'confidence': float(confidence),
            'feature_values': dict(zip(ORIGINAL_FEATURE_NAMES, features)),
            'analysis': {{
                'risk_level': 'High' if prediction > 0.8 else 'Medium' if prediction > 0.5 else 'Low',
                'confidence_level': 'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low',
                'trend': 'Stable'
            }}
        }}
    except Exception as e:
        logger.error(f"Prediction error: {{e}}")
        return {{
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'prediction': 0.0,
            'is_ddos': False,
            'confidence': 0.0
        }}
'''
    
    loader_path = artifact_dir / 'latest' / 'model_loader.py'
    loader_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(loader_path, 'w') as f:
        f.write(loader_code)
    
    logger.info(f"FastAPI loader created at {loader_path}")


def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(description='Train XGBoost model for DDoS detection')
    parser.add_argument('--data-path', type=str, default=None, help='Path to training data CSV')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size (default: 0.2)')
    parser.add_argument('--n-iter', type=int, default=20, help='Hyperparameter tuning iterations (default: 20)')
    parser.add_argument('--no-tuning', action='store_true', help='Skip hyperparameter tuning')
    parser.add_argument('--no-shap', action='store_true', help='Skip SHAP explanations')
    parser.add_argument('--target-col', type=str, default='target', help='Target column name (default: target)')
    parser.add_argument('--artifacts-dir', type=str, default=None, help='Artifacts directory')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("XGBoost Training Pipeline for DDoS Detection")
    logger.info("=" * 80)
    
    # Initialize components
    data_loader = DataLoader(data_path=args.data_path)
    feature_engineer = FeatureEngineer(auto_detect_windows=True)
    model_trainer = ModelTrainer(use_xgboost=XGBOOST_AVAILABLE)
    
    # Load and prepare data
    logger.info("Step 1: Loading data...")
    df = data_loader.load_data()
    
    # Determine target column
    target_col = args.target_col
    if target_col not in df.columns and 'class' in df.columns:
        target_col = 'class'
        logger.info(f"Using 'class' as target column")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Available columns: {df.columns.tolist()}")
    
    # Feature engineering
    logger.info("Step 2: Feature engineering...")
    df, feature_cols = feature_engineer.engineer_features(df, target_col=target_col)
    
    # Time-based split
    logger.info("Step 3: Time-based train/test split...")
    train_df, test_df = time_based_split(df, test_size=args.test_size, target_col=target_col)
    
    # Prepare features and targets
    X_train = train_df[feature_cols].values
    y_train = train_df[target_col].values
    X_test = test_df[feature_cols].values
    y_test = test_df[target_col].values
    
    model_trainer.feature_names = feature_cols
    
    # Train model
    logger.info("Step 4: Training model...")
    model = model_trainer.train(
        X_train, y_train, X_test, y_test,
        tune_hyperparameters=not args.no_tuning,
        n_iter=args.n_iter
    )
    
    # Make predictions
    logger.info("Step 5: Making predictions...")
    y_pred_proba = model_trainer.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    # Calculate metrics
    logger.info("Step 6: Calculating metrics...")
    artifact_manager = ArtifactManager(base_dir=Path(args.artifacts_dir) if args.artifacts_dir else None)
    metrics_calc = MetricsCalculator(artifact_manager.get_version_dir())
    metrics = metrics_calc.calculate_metrics(y_test, y_pred, y_pred_proba)
    
    # Create visualizations
    logger.info("Step 7: Creating visualizations...")
    metrics_calc.plot_confusion_matrix(y_test, y_pred, artifact_manager.get_version_dir() / 'plots' / 'confusion_matrix.png')
    metrics_calc.plot_roc_curve(y_test, y_pred_proba, artifact_manager.get_version_dir() / 'plots' / 'roc_curve.png')
    metrics_calc.plot_feature_importance(model, feature_cols, artifact_manager.get_version_dir() / 'plots' / 'feature_importance.png')
    
    # SHAP explanations
    if not args.no_shap and SHAP_AVAILABLE:
        logger.info("Step 8: Generating SHAP explanations...")
        shap_explainer = SHAPExplainer(artifact_manager.get_version_dir())
        shap_values = shap_explainer.explain(model, X_test, feature_cols)
    else:
        logger.info("Step 8: Skipping SHAP explanations")
    
    # Save artifacts
    logger.info("Step 9: Saving artifacts...")
    config = {
        'model_type': 'xgboost' if XGBOOST_AVAILABLE else 'gradient_boosting',
        'feature_count': len(feature_cols),
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'optimal_windows': feature_engineer.optimal_windows,
        'hyperparameter_tuning': not args.no_tuning,
        'timestamp': datetime.now().isoformat()
    }
    
    artifact_manager.save_model(
        model, model_trainer.scaler, feature_cols, metrics, config
    )
    
    # Create latest symlink
    artifact_manager.create_latest_symlink()
    
    # Create FastAPI loader
    logger.info("Step 10: Creating FastAPI loader...")
    create_fastapi_loader(artifact_manager.base_dir, artifact_manager.get_version_dir())
    
    # Print summary
    logger.info("=" * 80)
    logger.info("Training Summary")
    logger.info("=" * 80)
    logger.info(f"Model Type: {config['model_type']}")
    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Train Samples: {len(train_df)}")
    logger.info(f"Test Samples: {len(test_df)}")
    logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
    logger.info(f"Precision: {metrics['precision']:.4f}")
    logger.info(f"Recall: {metrics['recall']:.4f}")
    logger.info(f"F1 Score: {metrics['f1_score']:.4f}")
    logger.info(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"PR-AUC: {metrics['pr_auc']:.4f}")
    logger.info(f"Artifacts saved to: {artifact_manager.get_version_dir()}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()

