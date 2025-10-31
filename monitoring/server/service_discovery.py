"""
Service and Program Discovery Module
Automatically detects installed programs, services, and their log locations
"""

import os
import sys
import platform
import subprocess
import psutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """
    Discovers installed programs, services, and their log file locations
    """
    
    def __init__(self):
        self.system = platform.system().lower()
        self.discovered_services = {}
        self.log_locations = {}
        
    def discover_all_services(self) -> Dict[str, Any]:
        """
        Main discovery method - finds all services and programs
        """
        logger.info("Starting service discovery...")
        
        # Discover running processes
        running_processes = self.discover_running_processes()
        
        # Discover system services
        system_services = self.discover_system_services()
        
        # Discover installed applications
        installed_apps = self.discover_installed_applications()
        
        # Discover Python packages
        python_packages = self.discover_python_packages()
        
        # Discover web servers and databases
        web_db_services = self.discover_web_and_database_services()
        
        # Combine all discoveries
        self.discovered_services = {
            'running_processes': running_processes,
            'system_services': system_services,
            'installed_applications': installed_apps,
            'python_packages': python_packages,
            'web_database_services': web_db_services,
            'discovery_timestamp': datetime.now().isoformat(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine()
            }
        }
        
        # Discover log locations for all found services
        self.discover_all_log_locations()
        
        logger.info(f"Discovery complete. Found {len(self.log_locations)} services with logs")
        
        return self.discovered_services
    
    def discover_running_processes(self) -> List[Dict[str, Any]]:
        """
        Discover currently running processes
        """
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username']):
                try:
                    pinfo = proc.info
                    # Filter out system processes
                    if pinfo['name'] and not pinfo['name'].startswith('['):
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'exe': pinfo['exe'],
                            'cmdline': ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else '',
                            'username': pinfo['username']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logger.error(f"Error discovering processes: {e}")
        
        # Remove duplicates based on name
        unique_processes = {}
        for proc in processes:
            if proc['name'] not in unique_processes:
                unique_processes[proc['name']] = proc
        
        return list(unique_processes.values())
    
    def discover_system_services(self) -> List[Dict[str, Any]]:
        """
        Discover system services (Windows/Linux)
        """
        services = []
        
        if self.system == 'windows':
            services = self._discover_windows_services()
        elif self.system in ['linux', 'darwin']:
            services = self._discover_linux_services()
        
        return services
    
    def _discover_windows_services(self) -> List[Dict[str, Any]]:
        """
        Discover Windows services using PowerShell
        """
        services = []
        
        try:
            # Use PowerShell to get services
            cmd = ['powershell', '-Command', 
                   'Get-Service | Select-Object Name, DisplayName, Status | ConvertTo-Json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                service_data = json.loads(result.stdout)
                if isinstance(service_data, dict):
                    service_data = [service_data]
                
                for svc in service_data:
                    services.append({
                        'name': svc.get('Name', ''),
                        'display_name': svc.get('DisplayName', ''),
                        'status': svc.get('Status', 'Unknown'),
                        'type': 'windows_service'
                    })
        except Exception as e:
            logger.error(f"Error discovering Windows services: {e}")
        
        return services
    
    def _discover_linux_services(self) -> List[Dict[str, Any]]:
        """
        Discover Linux services using systemctl
        """
        services = []
        
        try:
            # Use systemctl to list services
            cmd = ['systemctl', 'list-units', '--type=service', '--all', '--no-pager']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '.service' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                'name': parts[0].replace('.service', ''),
                                'status': parts[2] if len(parts) > 2 else 'unknown',
                                'type': 'systemd_service'
                            })
        except Exception as e:
            logger.error(f"Error discovering Linux services: {e}")
        
        return services
    
    def discover_installed_applications(self) -> List[Dict[str, Any]]:
        """
        Discover installed applications
        """
        apps = []
        
        if self.system == 'windows':
            apps = self._discover_windows_apps()
        elif self.system in ['linux', 'darwin']:
            apps = self._discover_linux_apps()
        
        return apps
    
    def _discover_windows_apps(self) -> List[Dict[str, Any]]:
        """
        Discover installed Windows applications
        """
        apps = []
        
        try:
            # Check common installation directories
            program_dirs = [
                os.environ.get('ProgramFiles', 'C:\\Program Files'),
                os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'),
                os.environ.get('LOCALAPPDATA', ''),
            ]
            
            for prog_dir in program_dirs:
                if prog_dir and os.path.exists(prog_dir):
                    try:
                        for item in os.listdir(prog_dir):
                            item_path = os.path.join(prog_dir, item)
                            if os.path.isdir(item_path):
                                apps.append({
                                    'name': item,
                                    'path': item_path,
                                    'type': 'installed_application'
                                })
                    except PermissionError:
                        pass
        except Exception as e:
            logger.error(f"Error discovering Windows apps: {e}")
        
        return apps[:100]  # Limit to first 100
    
    def _discover_linux_apps(self) -> List[Dict[str, Any]]:
        """
        Discover installed Linux applications
        """
        apps = []
        
        try:
            # Check /usr/bin and /usr/local/bin
            bin_dirs = ['/usr/bin', '/usr/local/bin', '/opt']
            
            for bin_dir in bin_dirs:
                if os.path.exists(bin_dir):
                    try:
                        for item in os.listdir(bin_dir):
                            item_path = os.path.join(bin_dir, item)
                            if os.path.isfile(item_path) or os.path.isdir(item_path):
                                apps.append({
                                    'name': item,
                                    'path': item_path,
                                    'type': 'installed_application'
                                })
                    except PermissionError:
                        pass
        except Exception as e:
            logger.error(f"Error discovering Linux apps: {e}")
        
        return apps[:100]  # Limit to first 100
    
    def discover_python_packages(self) -> List[Dict[str, Any]]:
        """
        Discover installed Python packages
        """
        packages = []
        
        try:
            import pkg_resources
            
            for dist in pkg_resources.working_set:
                packages.append({
                    'name': dist.project_name,
                    'version': dist.version,
                    'location': dist.location,
                    'type': 'python_package'
                })
        except Exception as e:
            logger.error(f"Error discovering Python packages: {e}")
        
        return packages
    
    def discover_web_and_database_services(self) -> List[Dict[str, Any]]:
        """
        Discover common web servers and databases
        """
        services = []
        
        # Common service names to look for
        target_services = [
            'nginx', 'apache', 'httpd', 'apache2',
            'mysql', 'mariadb', 'postgresql', 'postgres', 'mongodb',
            'redis', 'memcached',
            'docker', 'containerd',
            'elasticsearch', 'kibana', 'logstash'
        ]
        
        # Check running processes
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                for target in target_services:
                    if target in proc_name:
                        services.append({
                            'name': proc.info['name'],
                            'type': 'web_database_service',
                            'status': 'running'
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return services
    
    def discover_all_log_locations(self):
        """
        Discover log file locations for all found services
        """
        logger.info("Discovering log locations...")
        
        # Common log directories by platform
        if self.system == 'windows':
            common_log_dirs = [
                'C:\\Windows\\Logs',
                'C:\\ProgramData\\logs',
                os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'logs'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'logs'),
            ]
        else:  # Linux/Mac
            common_log_dirs = [
                '/var/log',
                '/var/log/apache2',
                '/var/log/nginx',
                '/var/log/mysql',
                '/var/log/postgresql',
            ]
            
            # Also explicitly add common system log files
            explicit_log_files = [
                '/var/log/syslog',
                '/var/log/kern.log',
                '/var/log/auth.log',
                '/var/log/messages',
                '/var/log/daemon.log',
            ]
            
            # Check each explicit log file
            for log_file_path in explicit_log_files:
                log_file = Path(log_file_path)
                if log_file.exists() and log_file.is_file():
                    # Extract service name from filename
                    service_name = log_file.stem.replace('.', '_')
                    if service_name == 'kern':
                        service_name = 'kernel'
                    elif service_name == 'auth':
                        service_name = 'auth'
                    
                    if service_name not in self.log_locations:
                        self.log_locations[service_name] = []
                    
                    self.log_locations[service_name].append({
                        'path': str(log_file),
                        'size': log_file.stat().st_size,
                        'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    })
                    logger.debug(f"Found explicit log file: {log_file_path} for service: {service_name}")
        
        # Add current project logs
        project_root = Path(__file__).parent.parent.parent
        common_log_dirs.extend([
            str(project_root / 'logs'),
            str(project_root / 'model' / 'logs'),
            str(project_root / 'monitoring' / 'server' / 'logs'),
            str(project_root / 'incident-bot' / 'logs'),
            str(project_root / 'monitoring' / 'dashboard' / 'logs'),
        ])
        
        # Search for log files
        for log_dir in common_log_dirs:
            self._scan_directory_for_logs(log_dir)
        
        # Search in application directories
        for app in self.discovered_services.get('installed_applications', []):
            app_path = app.get('path', '')
            if app_path:
                # Check for logs subdirectory
                log_subdir = os.path.join(app_path, 'logs')
                if os.path.exists(log_subdir):
                    self._scan_directory_for_logs(log_subdir, app['name'])
    
    def _scan_directory_for_logs(self, directory: str, service_name: str = None):
        """
        Scan a directory for log files
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return
            
            # Special handling for /var/log - scan files directly
            if str(dir_path) == '/var/log':
                # Look for common system log files
                common_logs = ['syslog', 'kern.log', 'auth.log', 'messages', 'daemon.log', 'system.log']
                for log_name in common_logs:
                    log_file = dir_path / log_name
                    if log_file.exists() and log_file.is_file():
                        # Use log name as service name
                        svc_name = log_name.replace('.log', '').replace('.', '_')
                        if svc_name not in self.log_locations:
                            self.log_locations[svc_name] = []
                        
                        self.log_locations[svc_name].append({
                            'path': str(log_file),
                            'size': log_file.stat().st_size,
                            'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                        })
            
            # Find all .log files in directory
            for log_file in dir_path.rglob('*.log'):
                if log_file.is_file():
                    # Determine service name from file path
                    if not service_name:
                        # Use filename without extension as service name
                        service_name = log_file.stem
                        # For /var/log files, use cleaner names
                        if str(log_file.parent) == '/var/log':
                            if log_file.name == 'syslog':
                                service_name = 'syslog'
                            elif log_file.name == 'kern.log':
                                service_name = 'kernel'
                            elif log_file.name == 'auth.log':
                                service_name = 'auth'
                    
                    if service_name not in self.log_locations:
                        self.log_locations[service_name] = []
                    
                    self.log_locations[service_name].append({
                        'path': str(log_file),
                        'size': log_file.stat().st_size,
                        'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    })
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot access {directory}: {e}")
            pass  # Silently skip directories we can't access
    
    def get_log_locations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all discovered log locations
        """
        return self.log_locations
    
    def save_discovery_results(self, filename: str = 'service_discovery.json'):
        """
        Save discovery results to a JSON file
        """
        output = {
            'discovered_services': self.discovered_services,
            'log_locations': self.log_locations
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Discovery results saved to {filename}")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of discovered services
        """
        return {
            'total_running_processes': len(self.discovered_services.get('running_processes', [])),
            'total_system_services': len(self.discovered_services.get('system_services', [])),
            'total_installed_apps': len(self.discovered_services.get('installed_applications', [])),
            'total_python_packages': len(self.discovered_services.get('python_packages', [])),
            'total_web_db_services': len(self.discovered_services.get('web_database_services', [])),
            'total_services_with_logs': len(self.log_locations),
            'total_log_files': sum(len(logs) for logs in self.log_locations.values()),
            'platform': self.discovered_services.get('platform', {})
        }


if __name__ == "__main__":
    # Test the service discovery
    discovery = ServiceDiscovery()
    results = discovery.discover_all_services()
    
    # Print summary
    summary = discovery.get_summary()
    print("\n" + "="*60)
    print("SERVICE DISCOVERY SUMMARY")
    print("="*60)
    print(f"Platform: {summary['platform'].get('system')} {summary['platform'].get('release')}")
    print(f"Running Processes: {summary['total_running_processes']}")
    print(f"System Services: {summary['total_system_services']}")
    print(f"Installed Applications: {summary['total_installed_apps']}")
    print(f"Python Packages: {summary['total_python_packages']}")
    print(f"Web/DB Services: {summary['total_web_db_services']}")
    print(f"Services with Logs: {summary['total_services_with_logs']}")
    print(f"Total Log Files: {summary['total_log_files']}")
    print("="*60)
    
    # Save results
    discovery.save_discovery_results()
    
    # Show some log locations
    print("\nSample Log Locations:")
    for service, logs in list(discovery.log_locations.items())[:5]:
        print(f"\n{service}:")
        for log in logs[:3]:
            print(f"  - {log['path']} ({log['size']} bytes)")

