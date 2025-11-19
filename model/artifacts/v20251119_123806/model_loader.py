"""
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
