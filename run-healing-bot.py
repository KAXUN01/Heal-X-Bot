#!/usr/bin/env python3
"""
Healing-bot: Unified System Launcher
A single script to run the entire healing-bot system with Docker or native Python execution.
"""

import os
import sys
import subprocess
import platform
import time
import signal
import threading
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional

class HealingBotLauncher:
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.processes = []
        self.running = True
        self.project_root = Path(__file__).parent.absolute()
        
        # Service configurations
        self.services = {
            "model": {
                "name": "DDoS Model API",
                "port": 8080,
                "path": "model",
                "script": "main.py",
                "health_url": "http://localhost:8080/health",
                "docker_service": "model"
            },
            "network-analyzer": {
                "name": "Network Analyzer",
                "port": 8000,
                "path": "monitoring/server",
                "script": "network_analyzer.py",
                "health_url": "http://localhost:8000/active-threats",
                "docker_service": "network-analyzer"
            },
            "dashboard": {
                "name": "ML Dashboard",
                "port": 3001,
                "path": "monitoring/dashboard",
                "script": "app.py",
                "health_url": "http://localhost:3001/api/health",
                "docker_service": "dashboard"
            },
            "incident-bot": {
                "name": "Incident Bot",
                "port": 8000,
                "path": "incident-bot",
                "script": "main.py",
                "health_url": "http://localhost:8000/health",
                "docker_service": "incident-bot"
            },
            "monitoring-server": {
                "name": "Monitoring Server",
                "port": 5000,
                "path": "monitoring/server",
                "script": "app.py",
                "health_url": "http://localhost:5000/health",
                "docker_service": "server"
            },
            "healing-dashboard": {
                "name": "Healing Dashboard API",
                "port": 5001,
                "path": "monitoring/server",
                "script": "healing_dashboard_api.py",
                "health_url": "http://localhost:5001/api/health",
                "docker_service": "healing-dashboard"
            }
        }
        
        # Docker services (full stack)
        self.docker_services = [
            "model", "server", "network-analyzer", "dashboard", 
            "incident-bot", "healing-dashboard", "prometheus", "grafana"
        ]

    def print_banner(self):
        """Print the healing-bot banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    🛡️  HEALING-BOT  🛡️                      ║
║                                                              ║
║        AI-Powered DDoS Detection & IP Blocking System       ║
║                                                              ║
║  🧠 ML Detection  🚫 Auto Blocking  📊 Real-time Dashboard   ║
║  🤖 AI Response   📈 Analytics      🔍 Network Analysis     ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ ERROR: Python 3.8 or higher is required")
            return False
        print(f"✅ Python {sys.version.split()[0]} detected")
        
        # Check if Docker is available
        try:
            result = subprocess.run(["docker", "--version"], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ Docker detected: {result.stdout.strip()}")
            self.docker_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  Docker not available - will use native Python execution")
            self.docker_available = False
        
        # Check if Docker Compose is available
        if self.docker_available:
            try:
                result = subprocess.run(["docker-compose", "--version"], 
                                      capture_output=True, text=True, check=True)
                print(f"✅ Docker Compose detected: {result.stdout.strip()}")
                self.docker_compose_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  Docker Compose not available")
                self.docker_compose_available = False
        
        return True

    def setup_environment(self):
        """Setup environment and install dependencies"""
        print("🔧 Setting up environment...")
        
        # Create .env file if it doesn't exist
        env_file = self.project_root / ".env"
        env_template = self.project_root / "env.template"
        
        if not env_file.exists() and env_template.exists():
            print("📝 Creating .env file from template...")
            with open(env_template, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file - please configure your API keys")
        
        # Install critical dependencies first
        print("📦 Installing critical dependencies...")
        critical_deps = [
            "fastapi>=0.104.1", "uvicorn>=0.24.0", "flask>=3.0.0", "flask-bootstrap>=5.3.2.1",
            "requests>=2.31.0", "numpy>=1.24.3", "pandas>=2.0.3", "scikit-learn>=1.3.0",
            "tensorflow>=2.13.0", "matplotlib>=3.7.2", "seaborn>=0.12.2", "psutil>=5.9.6",
            "prometheus-client>=0.19.0", "websockets>=12.0",
            "python-multipart>=0.0.6", "jinja2>=3.1.2", "markupsafe>=2.1.3"
        ]
        
        try:
            print("🔧 Installing core dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install"] + critical_deps, 
                         check=True, cwd=self.project_root, capture_output=True)
            print("✅ Core dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Some core dependencies may not have installed properly")
        
        # Install from requirements files
        print("📦 Installing from requirements files...")
        
        # Install main requirements
        main_req_file = self.project_root / "requirements.txt"
        if main_req_file.exists():
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(main_req_file)], 
                             check=True, cwd=self.project_root, capture_output=True)
                print("✅ Main requirements installed")
            except subprocess.CalledProcessError:
                print("⚠️  Warning: Main requirements installation had issues")
        
        # Install component-specific requirements
        for service_id, config in self.services.items():
            req_file = self.project_root / config["path"] / "requirements.txt"
            if req_file.exists():
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], 
                                 check=True, cwd=self.project_root, capture_output=True)
                    print(f"✅ {config['name']} dependencies installed")
                except subprocess.CalledProcessError:
                    print(f"⚠️  Warning: {config['name']} dependencies had issues")
        
        # Final verification and fix any remaining issues
        print("🔍 Final dependency verification...")
        missing_deps = []
        critical_modules = ["fastapi", "uvicorn", "flask", "requests", "numpy", "pandas", "tensorflow"]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                missing_deps.append(module)
        
        if missing_deps:
            print(f"🔧 Installing remaining missing dependencies: {', '.join(missing_deps)}")
            try:
                # Try installing with specific versions
                fallback_deps = {
                    "fastapi": "fastapi==0.104.1",
                    "uvicorn": "uvicorn==0.24.0", 
                    "flask": "flask==3.0.0",
                    "requests": "requests==2.31.0",
                    "numpy": "numpy==1.24.3",
                    "pandas": "pandas==2.0.3",
                    "tensorflow": "tensorflow==2.13.0"
                }
                
                install_deps = [fallback_deps.get(dep, dep) for dep in missing_deps]
                subprocess.run([sys.executable, "-m", "pip", "install"] + install_deps, 
                             check=True, cwd=self.project_root, capture_output=True)
                print("✅ Missing dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Critical error: Could not install required dependencies")
                print(f"   Please run manually: pip install {' '.join(missing_deps)}")
                return False
        
        print("✅ All dependencies verified and ready")
        return True

    def check_ports(self) -> bool:
        """Check if required ports are available"""
        print("🔍 Checking port availability...")
        
        import socket
        
        ports_to_check = [8080, 8000, 3001, 5000, 5001, 9090, 3000]
        occupied_ports = []
        
        for port in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    occupied_ports.append(port)
                sock.close()
            except:
                pass
        
        if occupied_ports:
            print(f"⚠️  Warning: Ports {occupied_ports} are already in use")
            print("   The system may not start properly if these ports are needed")
        
        return True

    def start_docker_services(self):
        """Start services using Docker Compose"""
        print("🐳 Starting services with Docker Compose...")
        
        try:
            # Start all services
            cmd = ["docker-compose", "up", "-d"]
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            
            print("✅ Docker services started successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start Docker services: {e}")
            return False

    def start_native_services(self, services_to_start: List[str]):
        """Start services using native Python execution"""
        print("🐍 Starting services with native Python...")
        
        for service_id in services_to_start:
            if service_id not in self.services:
                print(f"⚠️  Unknown service: {service_id}")
                continue
                
            config = self.services[service_id]
            service_path = self.project_root / config["path"]
            script_path = service_path / config["script"]
            
            if not script_path.exists():
                print(f"❌ Script not found: {script_path}")
                continue
            
            print(f"🚀 Starting {config['name']}...")
            
            try:
                # Start the service
                # Use unbuffered output for better logging
                env = os.environ.copy()
                env['PYTHONUNBUFFERED'] = '1'
                
                if self.is_windows:
                    process = subprocess.Popen(
                        [sys.executable, "-u", str(script_path)],
                        cwd=service_path,
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                else:
                    process = subprocess.Popen(
                        [sys.executable, "-u", str(script_path)],
                        cwd=service_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env
                    )
                
                # Give the process a moment to start and check for immediate errors
                time.sleep(3)
                
                # Check if process is still running
                if process.poll() is None:
                    self.processes.append((service_id, process))
                    print(f"✅ {config['name']} started (PID: {process.pid})")
                else:
                    # Process exited immediately, likely due to missing dependencies
                    stdout, stderr = process.communicate()
                    print(f"❌ {config['name']} failed to start")
                    if stderr:
                        error_msg = stderr.decode('utf-8', errors='ignore')
                        if "ModuleNotFoundError" in error_msg:
                            print(f"   💡 Missing dependencies detected for {config['name']}")
                            print(f"   🔧 Attempting to fix dependencies...")
                            
                            # Try to install missing dependencies for this service
                            try:
                                req_file = service_path / "requirements.txt"
                                if req_file.exists():
                                    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], 
                                                 check=True, cwd=service_path, capture_output=True)
                                    print(f"   ✅ Dependencies installed for {config['name']}")
                                    
                                    # Try starting the service again
                                    print(f"   🔄 Retrying {config['name']}...")
                                    env = os.environ.copy()
                                    env['PYTHONUNBUFFERED'] = '1'
                                    
                                    if self.is_windows:
                                        retry_process = subprocess.Popen(
                                            [sys.executable, "-u", str(script_path)],
                                            cwd=service_path,
                                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                                            env=env
                                        )
                                    else:
                                        retry_process = subprocess.Popen(
                                            [sys.executable, "-u", str(script_path)],
                                            cwd=service_path,
                                            env=env
                                        )
                                    
                                    time.sleep(2)
                                    if retry_process.poll() is None:
                                        self.processes.append((service_id, retry_process))
                                        print(f"   ✅ {config['name']} started successfully on retry")
                                    else:
                                        print(f"   ❌ {config['name']} still failing after dependency fix")
                                else:
                                    print(f"   ❌ No requirements.txt found for {config['name']}")
                            except Exception as e:
                                print(f"   ❌ Failed to fix dependencies for {config['name']}: {e}")
                        else:
                            print(f"   Error: {error_msg[:200]}...")
                
            except Exception as e:
                print(f"❌ Failed to start {config['name']}: {e}")
        
        return len(self.processes) > 0

    def wait_for_services(self, services: List[str], timeout: int = 90):
        """Wait for services to become healthy"""
        print("⏳ Waiting for services to become ready...")
        
        try:
            import requests
        except ImportError:
            print("⚠️  requests module not available - skipping health checks")
            print("   Services may still be starting...")
            time.sleep(10)  # Give services time to start
            return True
        
        start_time = time.time()
        healthy_services = set()
        checked_services = set()
        
        while time.time() - start_time < timeout:
            for service_id in services:
                if service_id in healthy_services:
                    continue
                    
                if service_id in self.services:
                    config = self.services[service_id]
                    try:
                        response = requests.get(config["health_url"], timeout=2)
                        if response.status_code == 200:
                            healthy_services.add(service_id)
                            print(f"✅ {config['name']} is healthy")
                    except requests.exceptions.ConnectionError:
                        # Service not ready yet
                        if service_id not in checked_services:
                            checked_services.add(service_id)
                            print(f"⏳ Waiting for {config['name']}...")
                    except Exception as e:
                        # Other errors - log but continue
                        pass
            
            if len(healthy_services) == len(services):
                print("🎉 All services are healthy!")
                return True
            
            time.sleep(3)
        
        if len(healthy_services) > 0:
            print(f"✅ {len(healthy_services)}/{len(services)} services are healthy")
        else:
            print(f"⚠️  Services may still be starting - check manually")
        return len(healthy_services) > 0

    def print_access_info(self):
        """Print access information for all services"""
        print("\n" + "="*60)
        print("🌐 ACCESS POINTS")
        print("="*60)
        
        access_points = [
            ("📊 Dashboard", "http://localhost:3001", "Main monitoring dashboard"),
            ("🛡️ Healing Dashboard", "http://localhost:5001", "Healing bot dashboard"),
            ("🤖 Model API", "http://localhost:8080", "DDoS detection model"),
            ("🔍 Network Analyzer", "http://localhost:8000", "Network traffic analysis"),
            ("🚨 Incident Bot", "http://localhost:8000", "AI incident response"),
            ("📈 Monitoring Server", "http://localhost:5000", "System metrics"),
            ("📊 Prometheus", "http://localhost:9090", "Metrics collection"),
            ("📈 Grafana", "http://localhost:3000", "Advanced dashboards")
        ]
        
        for name, url, description in access_points:
            print(f"{name:<20} {url:<25} {description}")
        
        print("\n" + "="*60)
        print("🛡️  HEALING-BOT IS RUNNING!")
        print("="*60)
        print("Press Ctrl+C to stop all services")

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print("\n🛑 Shutting down services...")
            self.running = False
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def stop_all_services(self):
        """Stop all running services"""
        print("🛑 Stopping services...")
        
        # Stop native Python processes
        for service_id, process in self.processes:
            try:
                print(f"🛑 Stopping {self.services[service_id]['name']}...")
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        # Stop Docker services if they were started
        if hasattr(self, 'docker_started') and self.docker_started:
            try:
                print("🛑 Stopping Docker services...")
                subprocess.run(["docker-compose", "down"], cwd=self.project_root)
            except:
                pass
        
        print("✅ All services stopped")

    def run(self, mode: str = "auto", services: Optional[List[str]] = None):
        """Main run method"""
        self.print_banner()
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Setup environment
        if not self.setup_environment():
            return False
        
        # Check ports
        self.check_ports()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        # Determine execution mode
        if mode == "auto":
            use_docker = self.docker_available and self.docker_compose_available
        elif mode == "docker":
            use_docker = True
            if not self.docker_available:
                print("❌ Docker not available")
                return False
        else:  # native
            use_docker = False
        
        # Determine services to start
        if services is None:
            if use_docker:
                services_to_start = self.docker_services
            else:
                # Start all essential services in native mode
                services_to_start = ["model", "network-analyzer", "dashboard", "incident-bot", 
                                    "monitoring-server", "healing-dashboard"]
        else:
            services_to_start = services
        
        # Start services
        if use_docker:
            print(f"🐳 Using Docker mode")
            if not self.start_docker_services():
                return False
            self.docker_started = True
        else:
            print(f"🐍 Using native Python mode")
            if not self.start_native_services(services_to_start):
                return False
        
        # Wait for services to be ready
        self.wait_for_services(services_to_start)
        
        # Print access information
        self.print_access_info()
        
        # Keep running until interrupted
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all_services()
        
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Healing-bot: AI-Powered DDoS Detection System")
    parser.add_argument("--mode", choices=["auto", "docker", "native"], default="auto",
                       help="Execution mode: auto (detect), docker, or native")
    parser.add_argument("--services", nargs="+", 
                       help="Specific services to start (default: all)")
    parser.add_argument("--setup-only", action="store_true",
                       help="Only setup environment, don't start services")
    
    args = parser.parse_args()
    
    launcher = HealingBotLauncher()
    
    if args.setup_only:
        launcher.print_banner()
        launcher.check_dependencies()
        launcher.setup_environment()
        print("✅ Setup completed!")
        return
    
    launcher.run(mode=args.mode, services=args.services)

if __name__ == "__main__":
    main()
