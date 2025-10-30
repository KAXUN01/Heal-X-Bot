#!/bin/bash
echo "Starting Healing-bot components..."

echo "Starting Model API..."
cd model && python main.py &
MODEL_PID=$!

echo "Starting Network Analyzer..."
cd ../monitoring/server && python network_analyzer.py &
NETWORK_PID=$!

echo "Starting Dashboard..."
cd ../dashboard && python app.py &
DASHBOARD_PID=$!

echo "Starting Incident Bot..."
cd ../../incident-bot && python main.py &
INCIDENT_PID=$!

echo "All components started!"
echo ""
echo "Access points:"
echo "- Dashboard: http://localhost:3001"
echo "- Model API: http://localhost:8080"
echo "- Network Analyzer: http://localhost:8000"
echo "- Incident Bot: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "Stopping services..."
    kill $MODEL_PID $NETWORK_PID $DASHBOARD_PID $INCIDENT_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait
