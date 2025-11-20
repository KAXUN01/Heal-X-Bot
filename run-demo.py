#!/usr/bin/env python3
"""
Main Demo Script - AI Bot Prototype Demonstration
Demonstrates the complete autonomous detection, diagnosis, and healing cycle
"""

import sys
import time
import subprocess
import requests
from pathlib import Path

def print_banner():
    """Print demo banner"""
    print("\n" + "="*80)
    print("🤖 AI BOT PROTOTYPE - AUTONOMOUS SELF-HEALING DEMONSTRATION")
    print("="*80)
    print("\nThis demonstration will show:")
    print("  ✅ Real-time fault detection")
    print("  ✅ AI-powered root cause diagnosis")
    print("  ✅ Automatic self-healing")
    print("  ✅ Discord notifications")
    print("  ✅ Complete transparency and logging")
    print("\n" + "="*80 + "\n")

def check_services():
    """Check if required services are running"""
    print("🔍 Checking required services...")
    
    services = {
        'Dashboard API': 'http://localhost:5001/api/health',
        'Monitoring Server': 'http://localhost:5000/health',
    }
    
    all_ready = True
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"  ✅ {name} is running")
            else:
                print(f"  ⚠️  {name} returned status {response.status_code}")
                all_ready = False
        except:
            print(f"  ❌ {name} is not accessible")
            all_ready = False
    
    return all_ready

def start_cloud_simulation():
    """Start cloud simulation services"""
    print("\n☁️  Starting cloud simulation services...")
    
    project_root = Path(__file__).parent
    compose_file = project_root / 'config' / 'docker-compose-cloud-sim.yml'
    
    # Try docker compose (newer syntax) first
    try:
        result = subprocess.run(
            ['docker', 'compose', '-f', str(compose_file), 'up', '-d'],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            print("  ✅ Cloud simulation services started")
            print("  ⏳ Waiting for services to be ready...")
            time.sleep(10)
            return True
        else:
            print(f"  ⚠️  docker compose failed, trying docker-compose...")
    except FileNotFoundError:
        pass
    
    # Fallback to docker-compose (older syntax)
    try:
        result = subprocess.run(
            ['docker-compose', '-f', str(compose_file), 'up', '-d'],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            print("  ✅ Cloud simulation services started")
            print("  ⏳ Waiting for services to be ready...")
            time.sleep(10)
            return True
        else:
            print(f"  ❌ Failed to start services: {result.stderr}")
            return False
    except FileNotFoundError:
        print("  ❌ Docker Compose not available")
        print("     Install with: sudo apt install docker-compose")
        print("     Or use: sudo snap install docker")
        return False

def run_automated_demo():
    """Run the automated demo script"""
    print("\n🚀 Running automated demo...")
    
    project_root = Path(__file__).parent
    demo_script = project_root / 'scripts' / 'demo' / 'auto-demo-healing.py'
    
    try:
        # Use python3 explicitly
        python_cmd = 'python3' if sys.executable.endswith('python3') else sys.executable
        result = subprocess.run(
            [python_cmd, str(demo_script)],
            cwd=str(project_root),
            timeout=300
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("  ⚠️  Demo script timed out")
        return False
    except Exception as e:
        print(f"  ❌ Error running demo: {e}")
        return False

def main():
    """Main demo function"""
    print_banner()
    
    # Check if services are running
    if not check_services():
        print("\n⚠️  Some services are not running.")
        print("   Please start the healing bot system first:")
        print("   python3 run-healing-bot.py")
        print("\n   Or start individual services:")
        print("   - Dashboard API: python3 monitoring/server/healing_dashboard_api.py")
        print("   - Monitoring Server: python3 monitoring/server/app.py")
        return
    
    # Start cloud simulation
    if not start_cloud_simulation():
        print("\n⚠️  Cloud simulation services could not be started.")
        print("   You can start them manually:")
        print("   docker-compose -f config/docker-compose-cloud-sim.yml up -d")
        return
    
    # Run automated demo
    print("\n" + "="*80)
    print("🎬 STARTING AUTOMATED DEMONSTRATION")
    print("="*80 + "\n")
    
    success = run_automated_demo()
    
    if success:
        print("\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE!")
        print("="*80)
        print("\n📊 View the dashboard at: http://localhost:5001")
        print("   Navigate to the '☁️ Cloud Simulation' tab to see all visualizations")
        print("\n🔔 Check Discord for notifications (if configured)")
        print("\n💡 You can also manually inject faults using the dashboard")
        print("   or run: python scripts/demo/manual-fault-trigger.py --type crash")
        print("\n")
    else:
        print("\n⚠️  Demo encountered some issues. Check the logs above for details.")
        print("   You can still use the dashboard to manually test the system.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

