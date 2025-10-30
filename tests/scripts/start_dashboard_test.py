#!/usr/bin/env python3
"""
Simple script to start the dashboard for testing
"""
import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    try:
        import fastapi
        print("✓ FastAPI is available")
    except ImportError:
        print("✗ FastAPI not available")
        return False
    
    return True

def start_dashboard():
    """Start the dashboard"""
    print("Starting dashboard...")
    
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent / "monitoring" / "dashboard"
    os.chdir(dashboard_dir)
    
    print(f"Working directory: {os.getcwd()}")
    
    # Start the dashboard
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as e:
        print(f"Error starting dashboard: {e}")

def main():
    print("Dashboard Test Launcher")
    print("=" * 30)
    
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them first.")
        return
    
    print("\nStarting dashboard...")
    print("Press Ctrl+C to stop")
    start_dashboard()

if __name__ == "__main__":
    main()
