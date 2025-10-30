import numpy as np
import tensorflow as tf
import logging
import os
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pandas as pd
from sklearn.preprocessing import StandardScaler
import json

# Configure logging
logger = logging.getLogger(__name__)

# Create visualization directory if it doesn't exist
VIS_DIR = os.path.join(os.path.dirname(__file__), "visualizations")
os.makedirs(VIS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ddos_model.keras")

# Initialize scaler for feature normalization
scaler = StandardScaler()

# Load model
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    logger.info("DDoS detection model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load DDoS detection model: {str(e)}")
    model = None

# Historical predictions storage for trend analysis
prediction_history = {
    'timestamps': [],
    'predictions': [],
    'confidence': []
}

# Define key features for DDoS detection
FEATURE_NAMES = [
    "Protocol", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Fwd Packet Length Mean", "Bwd Packet Length Mean", "Flow IAT Mean",
    "Flow IAT Std", "Flow IAT Max", "Flow IAT Min", "Fwd IAT Mean",
    "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min", "Bwd IAT Mean",
    "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min", "Active Mean",
    "Active Std", "Active Max", "Active Min", "Idle Mean", "Idle Std",
    "Idle Max", "Idle Min"
]

def visualize_feature_importance(features: np.ndarray, prediction: float, timestamp: str) -> str:
    """Create feature importance visualization"""
    plt.figure(figsize=(12, 6))
    feature_values = pd.Series(features, index=FEATURE_NAMES)
    
    # Create bar plot of feature values
    sns.barplot(x=feature_values.values, y=feature_values.index)
    plt.title(f'Feature Importance (Prediction: {prediction:.3f})')
    plt.xlabel('Normalized Feature Value')
    
    # Save plot
    plot_path = os.path.join(VIS_DIR, f'feature_importance_{timestamp}.png')
    plt.savefig(plot_path)
    plt.close()
    return plot_path

def visualize_prediction_trend() -> str:
    """Create prediction trend visualization"""
    plt.figure(figsize=(12, 6))
    
    # Plot prediction history
    plt.plot(prediction_history['timestamps'], prediction_history['predictions'], 
             label='Prediction', marker='o')
    plt.axhline(y=0.5, color='r', linestyle='--', label='Decision Threshold')
    
    plt.title('DDoS Detection Trend')
    plt.xlabel('Time')
    plt.ylabel('Detection Probability')
    plt.xticks(rotation=45)
    plt.legend()
    
    # Save plot
    plot_path = os.path.join(VIS_DIR, 'prediction_trend.png')
    plt.savefig(plot_path)
    plt.close()
    return plot_path

def visualize_confidence_distribution() -> str:
    """Create confidence distribution visualization"""
    plt.figure(figsize=(10, 6))
    
    # Create confidence distribution plot
    sns.histplot(prediction_history['confidence'], bins=20, kde=True)
    plt.title('Prediction Confidence Distribution')
    plt.xlabel('Confidence Score')
    plt.ylabel('Frequency')
    
    # Save plot
    plot_path = os.path.join(VIS_DIR, 'confidence_distribution.png')
    plt.savefig(plot_path)
    plt.close()
    return plot_path

def extract_features_from_alert(alert_json: Dict[str, Any]) -> List[float]:
    """Extract DDoS detection features from alert JSON"""
    try:
        # Extract basic metrics
        metrics = alert_json.get('metrics', {})
        features = []
        
        # Map incoming metrics to feature list
        for feature in FEATURE_NAMES:
            value = metrics.get(feature.lower().replace(' ', '_'), 0.0)
            features.append(float(value))
            
        # Normalize features
        features = np.array(features).reshape(1, -1)
        normalized_features = scaler.fit_transform(features)
        
        return normalized_features.flatten().tolist()
        
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        return [0.0] * len(FEATURE_NAMES)

def predict_ddos(alert_json: Dict[str, Any]) -> Dict[str, Any]:
    """Predict DDoS probability and generate visualizations"""
    try:
        # Extract features
        features = extract_features_from_alert(alert_json)
        features_array = np.array(features).reshape(1, -1)
        
        # Make prediction
        if model is None:
            raise ValueError("Model not loaded")
            
        prediction = model.predict(features_array)[0][0]
        confidence = abs(prediction - 0.5) * 2  # Scale confidence 0-1
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Update prediction history
        prediction_history['timestamps'].append(timestamp)
        prediction_history['predictions'].append(prediction)
        prediction_history['confidence'].append(confidence)
        
        # Keep only last 100 predictions
        if len(prediction_history['timestamps']) > 100:
            prediction_history['timestamps'] = prediction_history['timestamps'][-100:]
            prediction_history['predictions'] = prediction_history['predictions'][-100:]
            prediction_history['confidence'] = prediction_history['confidence'][-100:]
        
        # Generate visualizations
        feature_plot = visualize_feature_importance(features, prediction, timestamp)
        trend_plot = visualize_prediction_trend()
        confidence_plot = visualize_confidence_distribution()
        
        # Prepare detailed response
        result = {
            'timestamp': timestamp,
            'prediction': float(prediction),
            'is_ddos': bool(prediction > 0.5),
            'confidence': float(confidence),
            'visualizations': {
                'feature_importance': feature_plot,
                'prediction_trend': trend_plot,
                'confidence_distribution': confidence_plot
            },
            'feature_values': dict(zip(FEATURE_NAMES, features)),
            'analysis': {
                'risk_level': 'High' if prediction > 0.8 else 'Medium' if prediction > 0.5 else 'Low',
                'confidence_level': 'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low',
                'trend': 'Increasing' if len(prediction_history['predictions']) > 1 and 
                        prediction > prediction_history['predictions'][-2] else 'Decreasing'
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'prediction': 0.0,
            'is_ddos': False,
            'confidence': 0.0
        }
