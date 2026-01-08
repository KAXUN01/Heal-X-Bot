#!/usr/bin/env python3
"""
Auto-Healing Presentation Demo Script
=====================================

This script demonstrates the complete auto-healing mechanism for presentations:
1. Injects two types of issues
2. Issue #1: Automatically fixable (service crash) - Click "Fix Issue" button
3. Issue #2: Requires manual intervention (disk full) - Click "Manual Steps" button

Usage:
    python scripts/demo/presentation-demo.py --inject-both
    python scripts/demo/presentation-demo.py --inject-fixable
    python scripts/demo/presentation-demo.py --inject-manual
    python scripts/demo/presentation-demo.py --cleanup
"""

import sys
import time
import argparse
import requests
import json
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style, Back

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'monitoring' / 'server'))

# Import healing components
try:
    from fault_injector import initialize_fault_injector
except ImportError as e:
    print(f"{Fore.RED}❌ Error importing fault_injector: {e}")
    print(f"{Fore.YELLOW}Make sure you're running from the project root directory")
    sys.exit(1)

# Configuration
DASHBOARD_URL = "http://localhost:5001"
API_URL = "http://localhost:5000"

def print_banner():
    """Print presentation demo banner"""
    print("\n" + "="*80)
    print(f"{Back.BLUE}{Fore.WHITE}{' '*80}")
    print(f"{Back.BLUE}{Fore.WHITE}{'🎯 AUTO-HEALING MECHANISM - PRESENTATION DEMO':^80}")
    print(f"{Back.BLUE}{Fore.WHITE}{' '*80}")
    print("="*80)
    print(f"\n{Fore.CYAN}📍 Dashboard URL: {Fore.WHITE}{DASHBOARD_URL}")
    print(f"{Fore.CYAN}📍 API URL: {Fore.WHITE}{API_URL}\n")

def print_step(step_num, title,emoji="🔷"):
    """Print step header"""
    print(f"\n{Fore.YELLOW}{'─'*80}")
    print(f"{Fore.YELLOW}{emoji} STEP {step_num}: {title}")
    print(f"{Fore.YELLOW}{'─'*80}")

def print_success(message):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {message}")

def print_error(message):
    """Print error message"""
    print(f"{Fore.RED}❌ {message}")

def print_info(message):
    """Print info message"""
    print(f"{Fore.CYAN}ℹ️  {message}")

def print_action(message):
    """Print action message"""
    print(f"{Fore.MAGENTA}⚡ {message}")

def check_services():
    """Check if required services are running"""
    print_step(0, "Checking Services", "🔍")
    
    services = {
        "Dashboard API": DASHBOARD_URL + "/api/health",
        "Monitoring API": API_URL + "/health"
    }
    
    all_healthy = True
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{service_name} is running")
            else:
                print_error(f"{service_name} returned status {response.status_code}")
                all_healthy = False
        except requests.exceptions.RequestException as e:
            print_error(f"{service_name} is not accessible: {e}")
            all_healthy = False
    
    if not all_healthy:
        print_error("\nSome services are not running!")
        print_info("Please start the services first:")
        print(f"{Fore.WHITE}    ./start.sh")
        print(f"{Fore.WHITE}    # or")
        print(f"{Fore.WHITE}    python run-healing-bot.py")
        return False
    
    print_success("\nAll required services are running!")
    return True

def inject_fixable_issue():
    """
    Inject Issue #1: Service Crash (Automatically Fixable)
    This will appear in the auto-healing page and can be fixed with "Fix Issue" button
    """
    print_step(1, "Injecting Fixable Issue (Service Crash)", "💥")
    
    try:
        fault_injector = initialize_fault_injector()
        
        # Try multiple container names (adaptable to different deploymentstyles)
        container_names = [
            "cloud-sim-api-server",
            "heal-x-bot-model-1",
            "heal-x-bot_model_1",
            "model"
        ]
        
        success = False
        for container_name in container_names:
            print_info(f"Attempting to crash container: {container_name}")
            result, message = fault_injector.inject_service_crash(container_name)
            
            if result:
                print_success(f"Service crash injected: {container_name}")
                print_success(message)
                success = True
                break
        
        if not success:
            print_error("Could not find any suitable container to crash")
            print_info("Available alternatives:")
            print(f"{Fore.WHITE}    1. Start cloud simulation services:")
            print(f"{Fore.WHITE}       docker compose -f config/docker-compose-cloud-sim.yml up -d")
            print(f"{Fore.WHITE}    2. Or inject a different fault type")
            return False
        
        print(f"\n{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN}✨ FIXABLE ISSUE INJECTED SUCCESSFULLY!")
        print(f"{Fore.GREEN}{'='*80}")
        print(f"\n{Fore.CYAN}📋 What happens next:")
        print(f"{Fore.WHITE}   1️⃣  The fault detector will detect the crashed service (~30 seconds)")
        print(f"{Fore.WHITE}   2️⃣  Issue appears in auto-healing page at {DASHBOARD_URL}")
        print(f"{Fore.WHITE}   3️⃣  Click '{Fore.GREEN}Fix Issue{Fore.WHITE}' button in the dashboard")
        print(f"{Fore.WHITE}   4️⃣  Auto-healer restarts the service automatically")
        print(f"{Fore.WHITE}   5️⃣  Verification confirms the fix worked")
        
        return True
        
    except Exception as e:
        print_error(f"Error injecting fixable issue: {e}")
        import traceback
        traceback.print_exc()
        return False

def inject_manual_issue():
    """
    Inject Issue #2: Disk Full (Requires Manual Steps)
    This will appear with manual instructions when automatic healing fails
    """
    print_step(2, "Injecting Manual Issue (Disk Full)", "💾")
    
    try:
        fault_injector = initialize_fault_injector()
        
        # Inject a smaller disk file to avoid filling actual disk
        size_gb = 0.5  # 500MB test file
        print_info(f"Creating test file of {size_gb}GB to simulate disk full...")
        
        success, message = fault_injector.inject_disk_full(size_gb)
        
        if success:
            print_success("Disk full condition injected")
            print_success(message)
        else:
            print_error(f"Failed to inject disk issue: {message}")
            return False
        
        print(f"\n{Fore.YELLOW}{'='*80}")
        print(f"{Fore.YELLOW}⚠️  MANUAL ISSUE INJECTED SUCCESSFULLY!")
        print(f"{Fore.YELLOW}{'='*80}")
        print(f"\n{Fore.CYAN}📋 What happens next:")
        print(f"{Fore.WHITE}   1️⃣  The fault detector detects low disk space (~30 seconds)")
        print(f"{Fore.WHITE}   2️⃣  Issue appears in auto-healing page")
        print(f"{Fore.WHITE}   3️⃣  Auto-healer attempts to fix but cannot fully resolve")
        print(f"{Fore.WHITE}   4️⃣  Click '{Fore.CYAN}Manual Steps{Fore.WHITE}' button")
        print(f"{Fore.WHITE}   5️⃣  Dashboard shows step-by-step manual instructions")
        
        return True
        
    except Exception as e:
        print_error(f"Error injecting manual issue: {e}")
        import traceback
        traceback.print_exc()
        return False

def inject_both_issues():
    """Inject both types of issues for complete demo"""
    print_banner()
    
    if not check_services():
        return False
    
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🎬 COMPLETE DEMO: Injecting Both Issue Types")
    print(f"{Fore.MAGENTA}{'='*80}\n")
    
    # Inject fixable issue first
    if not inject_fixable_issue():
        print_error("Failed to inject fixable issue")
        return False
    
    print(f"\n{Fore.CYAN}⏳ Waiting 10 seconds before injecting second issue...")
    time.sleep(10)
    
    # Inject manual issue
    if not inject_manual_issue():
        print_error("Failed to inject manual issue")
        return False
    
    print(f"\n{Fore.GREEN}{'='*80}")
    print(f"{Fore.GREEN}🎉 DEMO SETUP COMPLETE!")
    print(f"{Fore.GREEN}{'='*80}")
    print(f"\n{Fore.CYAN}📱 NOW OPEN THE DASHBOARD:")
    print(f"{Fore.WHITE}   {DASHBOARD_URL}")
    print(f"\n{Fore.CYAN}🎯 DEMONSTRATION STEPS:")
    print(f"{Fore.WHITE}   1. Wait 30-60 seconds for issues to appear in auto-healing page")
    print(f"{Fore.WHITE}   2. Click 'Fix Issue' on the service crash → See automatic healing")
    print(f"{Fore.WHITE}   3. Click 'Manual Steps' on disk full → See manual instructions")
    print(f"\n{Fore.YELLOW}💡 TIP: Refresh the dashboard page if issues don't appear immediately\n")
    
    return True

def cleanup_issues():
    """Cleanup all injected faults"""
    print_banner()
    print_step(0, "Cleaning Up Injected Faults", "🧹")
    
    try:
        fault_injector = initialize_fault_injector()
        success, message = fault_injector.cleanup_injected_faults()
        
        if success:
            print_success("All injected faults cleaned up")
            print_success(message)
        else:
            print_error(f"Cleanup failed: {message}")
            
        return success
        
    except Exception as e:
        print_error(f"Error during cleanup: {e}")
        return False

def wait_and_monitor():
    """Wait for issues to appear and monitor healing process"""
    print_step(3, "Monitoring Auto-Healing Process", "👀")
    
    print_info("Monitoring healing events (Ctrl+C to stop)...")
    print_info(f"Dashboard: {DASHBOARD_URL}")
    
    try:
        while True:
            # Check healing history via API
            try:
                response = requests.get(f"{API_URL}/api/healing/history", timeout=5)
                if response.status_code == 200:
                    history = response.json()
                    if history:
                        latest = history[0]
                        status = latest.get('status', 'unknown')
                        timestamp = latest.get('timestamp', 'unknown')
                        
                        if status == 'success':
                            print_success(f"[{timestamp}] Healing attempt succeeded")
                        elif status == 'failed':
                            print_error(f"[{timestamp}] Healing attempt failed")
                        else:
                            print_info(f"[{timestamp}] Healing in progress...")
            except:
                pass
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Auto-Healing Presentation Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full demo (both issues)
  python scripts/demo/presentation-demo.py --inject-both
  
  # Only fixable issue
  python scripts/demo/presentation-demo.py --inject-fixable
  
  # Only manual issue
  python scripts/demo/presentation-demo.py --inject-manual
  
  # Cleanup after demo
  python scripts/demo/presentation-demo.py --cleanup
  
  # Monitor healing process
  python scripts/demo/presentation-demo.py --monitor
        """
    )
    
    parser.add_argument('--inject-both', action='store_true',
                       help='Inject both fixable and manual issues (recommended)')
    parser.add_argument('--inject-fixable', action='store_true',
                       help='Inject only the fixable issue (service crash)')
    parser.add_argument('--inject-manual', action='store_true',
                       help='Inject only the manual issue (disk full)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Cleanup all injected faults')
    parser.add_argument('--monitor', action='store_true',
                       help='Monitor the healing process')
    
    args = parser.parse_args()
    
    # If no arguments, show help and run full demo
    if not any([args.inject_both, args.inject_fixable, args.inject_manual, 
                args.cleanup, args.monitor]):
        print_banner()
        print(f"{Fore.YELLOW}No arguments provided. Running FULL DEMO (--inject-both)")
        print(f"{Fore.CYAN}Use --help to see all options\n")
        time.sleep(2)
        args.inject_both = True
    
    try:
        if args.cleanup:
            cleanup_issues()
        elif args.monitor:
            wait_and_monitor()
        elif args.inject_both:
            inject_both_issues()
        elif args.inject_fixable:
            print_banner()
            if check_services():
                inject_fixable_issue()
        elif args.inject_manual:
            print_banner()
            if check_services():
                inject_manual_issue()
        
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Demo interrupted by user")
        print(f"{Fore.CYAN}Run with --cleanup to remove injected faults")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
