from fastapi import FastAPI, Request
from ddos_detector import predict_ddos
import logging
import requests
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DDoS Detection Model API", version="1.0.0")

# Set a sensible threshold; you can tune this later
DDOS_THRESHOLD = 0.7

# Prometheus metrics
ddos_detections_total = Counter('ddos_detections_total', 'Total number of DDoS detections', ['result'])
ddos_confidence_histogram = Histogram('ddos_confidence_histogram', 'DDoS detection confidence distribution')
ddos_prediction_histogram = Histogram('ddos_prediction_histogram', 'DDoS prediction score distribution')
ml_model_accuracy = Gauge('ml_model_accuracy', 'ML model accuracy percentage')
ml_model_precision = Gauge('ml_model_precision', 'ML model precision percentage')
ml_model_recall = Gauge('ml_model_recall', 'ML model recall percentage')
ml_model_f1_score = Gauge('ml_model_f1_score', 'ML model F1 score percentage')
ml_prediction_duration_seconds = Histogram('ml_prediction_duration_seconds', 'ML model prediction duration in seconds')
auto_blocks_total = Counter('auto_blocks_total', 'Total number of auto-blocked IPs')

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "DDoS Detection Model API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": True}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/alerts")
async def process_alert(request: Request):
    """Process network alert and detect DDoS attacks"""
    start_time = time.time()
    try:
        alert_json = await request.json()
        logger.info(f"Processing alert: {alert_json.get('id', 'unknown')}")
        
        # Use the predict_ddos function from ddos_detector
        result = predict_ddos(alert_json)
        
        # Record metrics
        prediction_duration = time.time() - start_time
        ml_prediction_duration_seconds.observe(prediction_duration)
        
        # Record detection result
        detection_result = "ddos" if result['is_ddos'] else "normal"
        ddos_detections_total.labels(result=detection_result).inc()
        
        # Record confidence and prediction scores
        ddos_confidence_histogram.observe(result['confidence'])
        ddos_prediction_histogram.observe(result['prediction'])
        
        # Set model performance metrics (these would typically come from model evaluation)
        ml_model_accuracy.set(0.95)  # Example values
        ml_model_precision.set(0.92)
        ml_model_recall.set(0.88)
        ml_model_f1_score.set(0.90)
        
        # Add detection results to the alert
        alert_json['ddos_detection'] = {
            'detected': result['is_ddos'],
            'confidence': result['confidence'],
            'prediction': result['prediction'],
            'risk_level': result['analysis']['risk_level'],
            'timestamp': result['timestamp']
        }
        
        # Auto-block IP if threat level is high
        if result['is_ddos'] and result['prediction'] >= 0.8:
            try:
                # Extract IP from alert (assuming it's in the alert data)
                source_ip = alert_json.get('source_ip', alert_json.get('ip', 'unknown'))
                if source_ip != 'unknown':
                    # Call network analyzer to block the IP
                    block_data = {
                        'ip': source_ip,
                        'reason': f"High DDoS threat level ({result['prediction']:.2f})",
                        'threat_level': result['prediction'],
                        'attack_type': 'DDoS Attack'
                    }
                    
                    # Try to block IP via network analyzer
                    try:
                        response = requests.post(
                            "http://network-analyzer:8000/block-ip",
                            json=block_data,
                            timeout=5
                        )
                        if response.status_code == 200:
                            logger.warning(f"Auto-blocked IP {source_ip} due to high DDoS threat level: {result['prediction']:.2f}")
                            alert_json['ddos_detection']['auto_blocked'] = True
                            auto_blocks_total.inc()
                        else:
                            logger.error(f"Failed to auto-block IP {source_ip}: {response.text}")
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Error calling network analyzer to block IP: {e}")
                        
            except Exception as e:
                logger.error(f"Error in auto-blocking logic: {e}")
        
        logger.info(f"DDoS detection result: {result['is_ddos']} (confidence: {result['confidence']:.3f})")
        
        return {
            "status": "alert processed",
            "ddos_detected": result['is_ddos'],
            "confidence": result['confidence'],
            "prediction": result['prediction'],
            "risk_level": result['analysis']['risk_level'],
            "visualizations": result.get('visualizations', {}),
            "alert": alert_json
        }
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "ddos_detected": False,
            "confidence": 0.0
        }

@app.get("/test")
async def test_model():
    """Test endpoint with sample data"""
    sample_alert = {
        "id": "test_001",
        "timestamp": "2024-01-01T12:00:00Z",
        "metrics": {
            "protocol": 6,
            "flow_duration": 1000,
            "total_fwd_packets": 100,
            "total_backward_packets": 50,
            "fwd_packet_length_mean": 1000,
            "bwd_packet_length_mean": 800,
            "flow_iat_mean": 100,
            "flow_iat_std": 50,
            "flow_iat_max": 200,
            "flow_iat_min": 50,
            "fwd_iat_mean": 100,
            "fwd_iat_std": 50,
            "fwd_iat_max": 200,
            "fwd_iat_min": 50,
            "bwd_iat_mean": 100,
            "bwd_iat_std": 50,
            "bwd_iat_max": 200,
            "bwd_iat_min": 50,
            "active_mean": 100,
            "active_std": 50,
            "active_max": 200,
            "active_min": 50,
            "idle_mean": 100,
            "idle_std": 50,
            "idle_max": 200,
            "idle_min": 50
        }
    }
    
    # Process the sample alert directly
    result = predict_ddos(sample_alert)
    
    return {
        "status": "test completed",
        "sample_alert": sample_alert,
        "ddos_detected": result['is_ddos'],
        "confidence": result['confidence'],
        "prediction": result['prediction'],
        "risk_level": result['analysis']['risk_level']
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("MODEL_PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
