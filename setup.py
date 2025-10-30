#!/usr/bin/env python3
"""
Healing-bot Setup Script
Simplified setup without Docker for development
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"OK: Python {sys.version.split()[0]} detected")

def install_requirements():
    """Install requirements for each component"""
    components = [
        ("incident-bot", "incident-bot/requirements.txt"),
        ("model", "model/requirements.txt"),
        ("monitoring/server", "monitoring/server/requirements.txt"),
        ("monitoring/dashboard", "monitoring/dashboard/requirements.txt")
    ]
    
    for component, req_file in components:
        if os.path.exists(req_file):
            print(f"Installing requirements for {component}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], 
                             check=True, capture_output=True)
                print(f"OK: {component} requirements installed")
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to install {component} requirements: {e}")
                return False
    return True

def create_directories():
    """Create necessary directories"""
    dirs = [
        "monitoring/server/static",
        "monitoring/server/templates",
        "model/visualizations",
        "monitoring/server/data"
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_start_scripts():
    """Create simplified start scripts"""
    
    # Windows batch file
    windows_script = """@echo off
echo Starting Healing-bot components...

echo Starting Model API...
start "Model API" cmd /k "cd model && python main.py"

echo Starting Network Analyzer...
start "Network Analyzer" cmd /k "cd monitoring/server && python network_analyzer.py"

echo Starting Dashboard...
start "Dashboard" cmd /k "cd monitoring/dashboard && python app.py"

echo Starting Incident Bot...
start "Incident Bot" cmd /k "cd incident-bot && python main.py"

echo All components started!
echo.
echo Access points:
echo - Dashboard: http://localhost:3001
echo - Model API: http://localhost:8080
echo - Network Analyzer: http://localhost:8000
echo - Incident Bot: http://localhost:8000
echo.
pause
"""
    
    with open("start-dev.bat", "w") as f:
        f.write(windows_script)
    
    # Linux/Mac shell script
    linux_script = """#!/bin/bash
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
"""
    
    with open("start-dev.sh", "w") as f:
        f.write(linux_script)
    
    # Make shell script executable
    if platform.system() != "Windows":
        os.chmod("start-dev.sh", 0o755)
    
    print("OK: Created start scripts: start-dev.bat (Windows) and start-dev.sh (Linux/Mac)")

def main():
    """Main setup function"""
    print("Healing-bot Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Install requirements
    print("\nInstalling requirements...")
    if not install_requirements():
        print("ERROR: Setup failed during requirements installation")
        sys.exit(1)
    
    # Create start scripts
    print("\nCreating start scripts...")
    create_start_scripts()
    
    print("\nSetup completed successfully!")
    print("\nTo start the system:")
    if platform.system() == "Windows":
        print("   Run: start-dev.bat")
    else:
        print("   Run: ./start-dev.sh")
    print("\nAccess points:")
    print("   - Dashboard: http://localhost:3001")
    print("   - Model API: http://localhost:8080")
    print("   - Network Analyzer: http://localhost:8000")
    print("   - Incident Bot: http://localhost:8000")

if __name__ == "__main__":
    main()
