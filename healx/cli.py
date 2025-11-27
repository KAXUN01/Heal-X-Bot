#!/usr/bin/env python3
"""
Heal-X-Bot CLI
Command-line interface for managing the Heal-X-Bot system
"""
import sys
import argparse
import subprocess
import json
import requests
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from monitoring.server.core.config import get_config
from monitoring.server.core.service_manager import get_service_manager


def print_banner():
    """Print the Heal-X-Bot banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🛡️  HEALING-BOT  🛡️                      ║
║                                                              ║
║        AI-Powered DDoS Detection & IP Blocking System       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def cmd_start(args):
    """Start all Heal-X-Bot services"""
    print_banner()
    print("🚀 Starting Heal-X-Bot services...\n")
    
    # Check if already running
    config = get_config()
    services = ['model', 'monitoring_server', 'healing_dashboard']
    
    already_running = False
    for service in services:
        try:
            if service == 'model':
                url = f'http://localhost:{config.model_port}/health'
            elif service == 'monitoring_server':
                url = f'http://localhost:{config.monitoring_server_port}/health'
            elif service == 'healing_dashboard':
                url = f'http://localhost:{config.healing_dashboard_port}/api/health'
            else:
                continue
            
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"⚠️  {service} is already running")
                already_running = True
        except:
            pass
    
    if already_running:
        print("\n⚠️  Some services are already running.")
        print("   Use 'python3 -m healx stop' to stop them first, or continue anyway?\n")
        return 0
    
    # Use existing startup script
    startup_script = project_root / 'start.sh'
    if startup_script.exists() and startup_script.is_file():
        print("📜 Using startup script: start.sh\n")
        try:
            # Make script executable
            startup_script.chmod(0o755)
            # Run the script in the foreground so output is visible
            subprocess.run(['bash', str(startup_script)], check=False)
        except KeyboardInterrupt:
            print("\n\n⚠️  Startup interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Error starting services: {e}")
            return 1
    else:
        print("❌ Startup script not found: start.sh")
        print("   Please ensure you're in the project root directory")
        return 1
    
    return 0


def cmd_stop(args):
    """Stop all Heal-X-Bot services"""
    print("🛑 Stopping Heal-X-Bot services...\n")
    
    # Stop via stop script if available
    stop_script = project_root / 'stop-services.sh'
    if stop_script.exists():
        subprocess.run(['bash', str(stop_script)])
        print("✅ All services stopped")
        return 0
    
    # Try to stop services via pkill
    services_to_stop = [
        'model/main.py',
        'monitoring/server/app.py',
        'monitoring/server/healing_dashboard_api.py',
        'network_analyzer.py',
        'incident-bot/main.py'
    ]
    
    for service in services_to_stop:
        try:
            subprocess.run(['pkill', '-f', service], check=False)
            print(f"✅ Stopped: {service}")
        except:
            pass
    
    print("✅ Services stopped")
    return 0


def cmd_status(args):
    """Check status of all services"""
    print_banner()
    print("📊 Service Status:\n")
    
    config = get_config()
    service_manager = get_service_manager(config)
    
    # Check service health
    services_to_check = {
        'Model API': f'http://localhost:{config.model_port}/health',
        'Monitoring Server': f'http://localhost:{config.monitoring_server_port}/health',
        'Healing Dashboard': f'http://localhost:{config.healing_dashboard_port}/api/health',
        'Network Analyzer': f'http://localhost:{config.network_analyzer_port}/active-threats',
    }
    
    all_healthy = True
    for name, url in services_to_check.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {name}: Running")
            else:
                print(f"⚠️  {name}: Responding but unhealthy (status: {response.status_code})")
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {name}: Not running")
            all_healthy = False
        except Exception as e:
            print(f"⚠️  {name}: Error checking ({str(e)})")
            all_healthy = False
    
    print()
    if all_healthy:
        print("✅ All services are running")
    else:
        print("⚠️  Some services are not running")
        return 1
    
    return 0


def cmd_logs(args):
    """View service logs"""
    service = args.service if hasattr(args, 'service') else None
    
    logs_dir = project_root / 'logs'
    if not logs_dir.exists():
        print(f"❌ Logs directory not found: {logs_dir}")
        return 1
    
    if service:
        log_file = logs_dir / f"{service}.log"
        if log_file.exists():
            print(f"📄 Showing logs for {service}:\n")
            subprocess.run(['tail', '-f', str(log_file)])
        else:
            print(f"❌ Log file not found: {log_file}")
            return 1
    else:
        # List all available log files
        print("📄 Available log files:\n")
        log_files = list(logs_dir.glob("*.log"))
        for log_file in sorted(log_files):
            print(f"  - {log_file.stem}")
        print("\nUse: healx logs <service_name> to view a specific log")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Heal-X-Bot CLI - Manage the Heal-X-Bot system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start all services')
    start_parser.set_defaults(func=cmd_start)
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop all services')
    stop_parser.set_defaults(func=cmd_stop)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check service status')
    status_parser.set_defaults(func=cmd_status)
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='View service logs')
    logs_parser.add_argument('service', nargs='?', help='Service name to view logs for')
    logs_parser.set_defaults(func=cmd_logs)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

