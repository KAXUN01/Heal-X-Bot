from fastapi import FastAPI, Request
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from datetime import datetime
import requests
import subprocess
import google.generativeai as genai
import re
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Load environment variables from .env file
load_dotenv()

# Set up logging using standardized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from monitoring.server.core.logging_config import setup_logger
    log_dir = Path(__file__).parent.parent / "logs"
    logger = setup_logger(
        name="incident_bot",
        log_file="incident_bot.log",
        log_dir=str(log_dir),
        console_output=True
    )
except ImportError:
    # Fallback to basic logging if core module not available
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "incident_bot.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("incident_bot")

# Initialize Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# If no API key is set, provide a warning
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. AI suggestions will be disabled.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize Slack webhook (optional)
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

# Configure self-healing settings
SELF_HEALING_ENABLED = os.getenv("SELF_HEALING_ENABLED", "false").lower() == "true"
SELF_HEALING_CONFIDENCE_THRESHOLD = float(os.getenv("SELF_HEALING_CONFIDENCE_THRESHOLD", "0.8"))

# S3 upload feature has been removed

app = FastAPI(title="AI-Powered Incident Bot")

# Prometheus metrics
incident_alerts_total = Counter('incident_alerts_total', 'Total number of incident alerts processed')
incident_responses_total = Counter('incident_responses_total', 'Total number of incident responses generated')
ai_suggestions_total = Counter('ai_suggestions_total', 'Total number of AI suggestions generated')
self_healing_actions_total = Counter('self_healing_actions_total', 'Total number of self-healing actions taken')
incident_processing_duration_seconds = Histogram('incident_processing_duration_seconds', 'Time spent processing incidents')
ai_response_time_seconds = Histogram('ai_response_time_seconds', 'Time spent generating AI responses')

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online", 
        "message": "AI-Powered Incident Bot is running",
        "ai_enabled": bool(GEMINI_API_KEY),
        "self_healing_enabled": SELF_HEALING_ENABLED
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "incident-bot",
        "ai_enabled": bool(GEMINI_API_KEY),
        "self_healing_enabled": SELF_HEALING_ENABLED
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def get_ai_suggestion(alert_info):
    """Get an AI-powered suggestion for the alert using Gemini"""
    start_time = time.time()
    try:
        if not GEMINI_API_KEY:
            return "AI suggestions disabled. Set GEMINI_API_KEY environment variable.", 0.0
        
        # Create a prompt with detailed information about the alert
        prompt = f"""
        You are an AI-powered DevOps engineer. You've received the following alert:
        
        {json.dumps(alert_info, indent=2)}
        
        Based on this alert, please suggest:
        1. What might be causing this issue
        2. Steps to remediate the problem
        3. How to prevent this in the future
        
        Keep your suggestion concise and actionable. If you can suggest specific commands, please do so.
        Start your response with a confidence score between 0 and 1 on a separate line (e.g. "CONFIDENCE: 0.8"),
        indicating how confident you are in your suggestion.
        """
        
        # Call Gemini API - using Gemini 2.0 Flash-Lite for explainable AI
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt)
        
        suggestion = response.text
        
        # Extract confidence score (matches decimal numbers 0.0 to 1.0)
        # Pattern matches: 0.0, 0.8, 1.0, etc. (requires decimal point)
        # For 1.0, only allows trailing zeros (1.0, 1.00, etc.), not 1.01, 1.1, etc.
        # Uses lookahead to ensure 1.0+ is followed by whitespace/end/non-digit without capturing it
        confidence_match = re.search(r"CONFIDENCE:\s*((?:0\.\d+|1\.0+))(?=\s|$|\D)", suggestion)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.0
        
        # Remove the confidence line from the suggestion
        # Pattern handles multiple cases:
        # 1. CONFIDENCE: X.XX\n (with newline)
        # 2. CONFIDENCE: X.XX (no newline, at end of text)
        # 3. CONFIDENCE: X.XX (no newline, followed by text)
        # 4. CONFIDENCE: X.XX\n\n (with multiple newlines)
        if confidence_match:
            # Match CONFIDENCE: followed by number, then optional whitespace and optional newline(s)
            # Use [\r\n]* to match any combination of newlines (including \r\n, \n, \r)
            # For 1.0, only allows trailing zeros (1.0, 1.00, etc.), not 1.01, 1.1, etc.
            # Uses lookahead to ensure 1.0+ is followed by whitespace/end/non-digit without capturing it
            suggestion = re.sub(r"CONFIDENCE:\s*(?:0\.\d+|1\.0+)(?=\s|$|\D)\s*[\r\n]*", "", suggestion, 1)
        
        # Record metrics
        ai_suggestions_total.inc()
        ai_response_time_seconds.observe(time.time() - start_time)
        
        return suggestion, confidence
        
    except Exception as e:
        logger.error(f"Error getting AI suggestion: {str(e)}", exc_info=True)
        return f"Error generating AI suggestion: {str(e)}", 0.0

def send_to_slack(message):
    """Send a message to Slack"""
    if not SLACK_WEBHOOK:
        logger.warning("Slack webhook not configured. Skipping notification.")
        return
    
    try:
        # Format message for Slack
        slack_payload = {
            "text": message,
            "mrkdwn": True
        }
        
        response = requests.post(
            SLACK_WEBHOOK,
            json=slack_payload
        )
        response.raise_for_status()
        logger.info("Successfully sent message to Slack")
    except Exception as e:
        logger.error(f"Error sending to Slack: {str(e)}", exc_info=True)


def attempt_self_healing(alert_info, suggestion, confidence):
    """Attempt to automatically remediate the issue based on the AI suggestion"""
    if not SELF_HEALING_ENABLED:
        return "Self-healing disabled", False
    
    if confidence < SELF_HEALING_CONFIDENCE_THRESHOLD:
        return f"Confidence too low for self-healing: {confidence} < {SELF_HEALING_CONFIDENCE_THRESHOLD}", False
    
    # Extract alert name and severity
    alert_name = alert_info.get("labels", {}).get("alertname", "unknown")
    
    # Apply remediation based on alert type
    healing_result = "No healing action taken"
    success = False
    
    try:
        # Handle high CPU usage
        if alert_name == "HighCPUUsage" or alert_name == "HighSimulatedCPULoad":
            # Simple example: for demo purposes, we'll just log that we would scale
            logger.info("⚠️ SELF-HEALING: Would automatically scale the service")
            
            # In a real system, you might use kubectl, AWS CLI, or other tools:
            # subprocess.run(["kubectl", "scale", "deployment", "my-app", "--replicas=5"])
            
            healing_result = "Simulated scaling the service to handle high CPU load"
            success = True
            
        # Handle high memory usage
        elif alert_name == "HighMemoryUsage":
            logger.info("⚠️ SELF-HEALING: Would restart the memory-intensive service")
            
            # In a real system:
            # subprocess.run(["kubectl", "rollout", "restart", "deployment/memory-intensive-app"])
            
            healing_result = "Simulated restarting memory-intensive service"
            success = True
            
        # Handle disk space issues
        elif alert_name == "LowDiskSpace":
            logger.info("⚠️ SELF-HEALING: Would clean up temp files")
            
            # In a real system:
            # subprocess.run(["ssh", "server", "find /tmp -type f -atime +7 -delete"])
            
            healing_result = "Simulated cleaning up temporary files to free disk space"
            success = True
            
        # Log the healing action
        with open("healing_actions.jsonl", "a") as f:
            action_record = {
                "timestamp": datetime.now().isoformat(),
                "alert": alert_info,
                "confidence": confidence,
                "action": healing_result,
                "success": success
            }
            f.write(json.dumps(action_record) + "\n")
        
        # Record metrics
        if success:
            self_healing_actions_total.inc()
            
        return healing_result, success
        
    except Exception as e:
        logger.error(f"Error during self-healing: {str(e)}", exc_info=True)
        return f"Self-healing error: {str(e)}", False

@app.post("/alert")
async def receive_alert(request: Request):
    """Main endpoint for receiving alerts from Alertmanager"""
    start_time = time.time()
    try:
        # Get the alert data
        data = await request.json()
        logger.info(f"Received alert webhook: {json.dumps(data, indent=2)}")
        
        # Extract key information
        alerts = data.get("alerts", [])
        response_data = {"processed_alerts": []}
        
        # Record metrics
        incident_alerts_total.inc(len(alerts))
        
        # Process each alert
        for i, alert in enumerate(alerts):
            alert_info = {
                "status": alert.get("status", "unknown"),
                "labels": alert.get("labels", {}),
                "annotations": alert.get("annotations", {})
            }
            
            # Get AI-powered suggestion
            suggestion, confidence = get_ai_suggestion(alert_info)
            
            # Attempt self-healing if appropriate
            healing_result, healing_success = attempt_self_healing(alert_info, suggestion, confidence)
            
            # Prepare message for Slack
            alert_name = alert_info["labels"].get("alertname", "Unknown Alert")
            instance = alert_info["labels"].get("instance", "Unknown Instance")
            description = alert_info["annotations"].get("description", "No description")
            
            slack_message = f"""
:rotating_light: *ALERT: {alert_name}*
:satellite: Instance: {instance}
:bar_chart: Status: {alert_info['status']}
:memo: Description: {description}

:bulb: *AI Suggestion* (Confidence: {confidence:.2f}):
```
{suggestion}
```

:wrench: *Self-Healing*: {healing_result if SELF_HEALING_ENABLED else "Disabled"}
            """
            
            # Send to Slack if configured
            send_to_slack(slack_message)
            
            # Store alert for future reference
            alert_record = {
                "timestamp": datetime.now().isoformat(),
                "alert_info": alert_info,
                "suggestion": suggestion,
                "confidence": confidence,
                "healing_result": healing_result,
                "healing_success": healing_success
            }
            
            # Store locally
            with open("alerts_processed.jsonl", "a") as f:
                record_line = json.dumps(alert_record) + "\n"
                f.write(record_line)
                
            # Add to response
            response_data["processed_alerts"].append({
                "alert_name": alert_name,
                "suggestion_summary": suggestion.split("\n")[0] if suggestion else "",
                "confidence": confidence,
                "self_healing": {"action": healing_result, "success": healing_success}
            })
        
        # Record processing duration
        processing_duration = time.time() - start_time
        incident_processing_duration_seconds.observe(processing_duration)
        
        return {
            "status": "success", 
            "message": f"Processed {len(alerts)} alerts with AI suggestions", 
            "timestamp": datetime.now().isoformat(),
            "data": response_data
        }
        
    except Exception as e:
        logger.error(f"Error processing alert: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

def validate_environment():
    """Validate that all required environment variables are set"""
    # Make all variables optional; warn instead of failing
    required_vars = ["GEMINI_API_KEY", "SLACK_WEBHOOK"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(f"Missing optional environment variables: {', '.join(missing_vars)}")
        logger.warning("AI suggestions and/or Slack notifications may be disabled.")
    
    
    return len(missing_vars) == 0

if __name__ == "__main__":
    # Validate environment but do not exit if optional vars are missing
    validate_environment()
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting AI-Powered Incident Bot on {host}:{port}")
    logger.info(f"AI Suggestions: {'Enabled' if GEMINI_API_KEY else 'Disabled'}")
    logger.info(f"Self-Healing: {'Enabled' if SELF_HEALING_ENABLED else 'Disabled'}")
    
    uvicorn.run(app, host=host, port=port)
