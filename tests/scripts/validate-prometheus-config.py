#!/usr/bin/env python3
"""
Validate Prometheus configuration files and setup
Tests configuration without requiring running services
"""

import os
import yaml
import json
import re
from pathlib import Path

class PrometheusConfigValidator:
    def __init__(self):
        self.project_root = Path(".")
        self.results = {}
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"[VALIDATE] {title}")
        print(f"{'='*60}")
        
    def print_success(self, message):
        print(f"[SUCCESS] {message}")
        
    def print_error(self, message):
        print(f"[ERROR] {message}")
        
    def print_warning(self, message):
        print(f"[WARNING] {message}")
        
    def print_info(self, message):
        print(f"[INFO] {message}")
        
    def validate_prometheus_config(self):
        """Validate prometheus.yml configuration"""
        self.print_header("Validating Prometheus Configuration")
        
        prometheus_file = self.project_root / "monitoring" / "prometheus" / "prometheus.yml"
        
        if not prometheus_file.exists():
            self.print_error(f"Prometheus config file not found: {prometheus_file}")
            return False
            
        try:
            with open(prometheus_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.print_success(f"Prometheus config file found and valid YAML")
            
            # Check scrape_configs
            scrape_configs = config.get('scrape_configs', [])
            healing_bot_jobs = []
            
            for job in scrape_configs:
                job_name = job.get('job_name', '')
                if 'healing-bot' in job_name or job_name == 'prometheus':
                    healing_bot_jobs.append(job)
                    targets = job.get('static_configs', [{}])[0].get('targets', [])
                    self.print_info(f"  Job: {job_name} -> Targets: {targets}")
            
            if len(healing_bot_jobs) >= 5:
                self.print_success(f"Found {len(healing_bot_jobs)} healing-bot scrape jobs")
                return True
            else:
                self.print_warning(f"Only found {len(healing_bot_jobs)} healing-bot jobs (expected 5+)")
                return False
                
        except Exception as e:
            self.print_error(f"Error reading Prometheus config: {e}")
            return False
    
    def validate_service_metrics(self):
        """Validate that all services have metrics endpoints"""
        self.print_header("Validating Service Metrics Configuration")
        
        services = {
            "model": "model/main.py",
            "incident-bot": "incident-bot/main.py", 
            "network-analyzer": "monitoring/server/network_analyzer.py",
            "dashboard": "monitoring/dashboard/app.py"
        }
        
        results = {}
        
        for service_name, file_path in services.items():
            service_file = self.project_root / file_path
            
            if not service_file.exists():
                self.print_error(f"Service file not found: {service_file}")
                results[service_name] = False
                continue
                
            try:
                with open(service_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for prometheus imports
                has_prometheus_import = 'from prometheus_client import' in content
                has_metrics_endpoint = '@app.get("/metrics")' in content or '@app.route("/metrics")' in content
                has_metrics_definition = 'Counter(' in content or 'Gauge(' in content or 'Histogram(' in content
                
                if has_prometheus_import and has_metrics_endpoint and has_metrics_definition:
                    self.print_success(f"{service_name}: Prometheus metrics configured")
                    results[service_name] = True
                else:
                    missing = []
                    if not has_prometheus_import:
                        missing.append("prometheus_client import")
                    if not has_metrics_endpoint:
                        missing.append("/metrics endpoint")
                    if not has_metrics_definition:
                        missing.append("metrics definitions")
                    
                    self.print_warning(f"{service_name}: Missing {', '.join(missing)}")
                    results[service_name] = False
                    
            except Exception as e:
                self.print_error(f"Error reading {service_name}: {e}")
                results[service_name] = False
        
        success_count = sum(results.values())
        total_count = len(results)
        
        if success_count == total_count:
            self.print_success(f"All {total_count} services have Prometheus metrics configured")
            return True
        else:
            self.print_warning(f"Only {success_count}/{total_count} services have metrics configured")
            return False
    
    def validate_requirements_files(self):
        """Validate that all requirements files include prometheus-client"""
        self.print_header("Validating Requirements Files")
        
        requirements_files = [
            "model/requirements.txt",
            "incident-bot/requirements.txt", 
            "monitoring/server/requirements.txt",
            "monitoring/dashboard/requirements.txt"
        ]
        
        results = {}
        
        for req_file in requirements_files:
            file_path = self.project_root / req_file
            
            if not file_path.exists():
                self.print_error(f"Requirements file not found: {file_path}")
                results[req_file] = False
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if 'prometheus-client' in content:
                    self.print_success(f"{req_file}: prometheus-client dependency found")
                    results[req_file] = True
                else:
                    self.print_warning(f"{req_file}: prometheus-client dependency missing")
                    results[req_file] = False
                    
            except Exception as e:
                self.print_error(f"Error reading {req_file}: {e}")
                results[req_file] = False
        
        success_count = sum(results.values())
        total_count = len(results)
        
        if success_count == total_count:
            self.print_success(f"All {total_count} requirements files include prometheus-client")
            return True
        else:
            self.print_warning(f"Only {success_count}/{total_count} requirements files include prometheus-client")
            return False
    
    def validate_grafana_dashboard(self):
        """Validate Grafana dashboard configuration"""
        self.print_header("Validating Grafana Dashboard")
        
        grafana_file = self.project_root / "grafana.json"
        
        if not grafana_file.exists():
            self.print_error(f"Grafana dashboard file not found: {grafana_file}")
            return False
            
        try:
            with open(grafana_file, 'r') as f:
                dashboard = json.load(f)
            
            panels = dashboard.get('panels', [])
            self.print_success(f"Grafana dashboard found with {len(panels)} panels")
            
            # Check for healing-bot specific metrics in queries
            healing_metrics = []
            for panel in panels:
                targets = panel.get('targets', [])
                for target in targets:
                    expr = target.get('expr', '')
                    if any(metric in expr for metric in ['ddos_', 'incident_', 'attack_', 'ip_', 'dashboard_', 'geographic_']):
                        healing_metrics.append(expr)
            
            if healing_metrics:
                self.print_success(f"Found {len(healing_metrics)} healing-bot metric queries in dashboard")
                return True
            else:
                self.print_warning("No healing-bot specific metrics found in dashboard queries")
                return False
                
        except Exception as e:
            self.print_error(f"Error reading Grafana dashboard: {e}")
            return False
    
    def validate_docker_compose(self):
        """Validate Docker Compose configuration"""
        self.print_header("Validating Docker Compose Configuration")
        
        compose_file = self.project_root / "docker-compose.yml"
        
        if not compose_file.exists():
            self.print_error(f"Docker Compose file not found: {compose_file}")
            return False
            
        try:
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            services = compose_config.get('services', {})
            self.print_success(f"Docker Compose file found with {len(services)} services")
            
            # Check for healing-bot services
            healing_services = []
            for service_name, service_config in services.items():
                if any(keyword in service_name for keyword in ['model', 'incident', 'network', 'dashboard', 'server', 'prometheus']):
                    healing_services.append(service_name)
                    ports = service_config.get('ports', [])
                    self.print_info(f"  Service: {service_name} -> Ports: {ports}")
            
            if len(healing_services) >= 5:
                self.print_success(f"Found {len(healing_services)} healing-bot services in Docker Compose")
                return True
            else:
                self.print_warning(f"Only found {len(healing_services)} healing-bot services (expected 5+)")
                return False
                
        except Exception as e:
            self.print_error(f"Error reading Docker Compose file: {e}")
            return False
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        self.print_header("VALIDATION REPORT SUMMARY")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result.get('success', False))
        
        print(f"[SUMMARY] Total Tests: {total_tests}")
        print(f"[SUMMARY] Passed: {passed_tests}")
        print(f"[SUMMARY] Failed: {total_tests - passed_tests}")
        print(f"[SUMMARY] Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n[RESULTS] Detailed Results:")
        for test_name, result in self.results.items():
            status = "[PASS]" if result.get('success', False) else "[FAIL]"
            print(f"  {status} {test_name}")
            if result.get('details'):
                print(f"    Details: {result['details']}")
    
    def generate_testing_instructions(self):
        """Generate instructions for testing the complete setup"""
        self.print_header("TESTING INSTRUCTIONS")
        
        print("[INSTRUCTIONS] To test the complete Prometheus setup:")
        print("1. Start all services: docker-compose up -d")
        print("2. Wait 2-3 minutes for services to fully initialize")
        print("3. Check service health:")
        print("   - Model API: http://localhost:8080/health")
        print("   - Network Analyzer: http://localhost:8000/")
        print("   - Incident Bot: http://localhost:8000/")
        print("   - Dashboard: http://localhost:3001/")
        print("   - Monitoring Server: http://localhost:5000/")
        print("4. Check metrics endpoints:")
        print("   - Model API: http://localhost:8080/metrics")
        print("   - Network Analyzer: http://localhost:8000/metrics")
        print("   - Incident Bot: http://localhost:8000/metrics")
        print("   - Dashboard: http://localhost:3001/metrics")
        print("   - Monitoring Server: http://localhost:5000/metrics")
        print("5. Check Prometheus targets: http://localhost:9090/targets")
        print("6. Check Prometheus metrics: http://localhost:9090/graph")
        print("7. Access Grafana: http://localhost:3000")
        print("8. Import the grafana.json dashboard")
        
        print(f"\n[COMMANDS] Useful Docker commands:")
        print("  docker-compose up -d                    # Start all services")
        print("  docker-compose ps                        # Check service status")
        print("  docker-compose logs [service-name]       # Check service logs")
        print("  docker-compose down                       # Stop all services")
        print("  docker-compose restart [service-name]    # Restart specific service")
    
    def run_validation(self):
        """Run complete validation"""
        self.print_header("HEALING-BOT PROMETHEUS CONFIGURATION VALIDATION")
        
        # Test 1: Prometheus Configuration
        prometheus_success = self.validate_prometheus_config()
        self.results['prometheus_config'] = {'success': prometheus_success}
        
        # Test 2: Service Metrics
        metrics_success = self.validate_service_metrics()
        self.results['service_metrics'] = {'success': metrics_success}
        
        # Test 3: Requirements Files
        requirements_success = self.validate_requirements_files()
        self.results['requirements_files'] = {'success': requirements_success}
        
        # Test 4: Grafana Dashboard
        grafana_success = self.validate_grafana_dashboard()
        self.results['grafana_dashboard'] = {'success': grafana_success}
        
        # Test 5: Docker Compose
        docker_success = self.validate_docker_compose()
        self.results['docker_compose'] = {'success': docker_success}
        
        # Generate reports
        self.generate_validation_report()
        self.generate_testing_instructions()
        
        # Final recommendation
        if all(result.get('success', False) for result in self.results.values()):
            self.print_header("CONFIGURATION VALIDATION PASSED!")
            print("[SUCCESS] All Prometheus configuration files are valid!")
            print("[SUCCESS] All services are configured with metrics endpoints!")
            print("[SUCCESS] All requirements files include prometheus-client!")
            print("[SUCCESS] Grafana dashboard is configured with healing-bot metrics!")
            print("[SUCCESS] Docker Compose is configured for all services!")
            print("\n[SUCCESS] Your Prometheus setup is ready for testing!")
        else:
            self.print_header("CONFIGURATION VALIDATION FAILED")
            print("[ERROR] Some configuration issues were found")
            print("[ERROR] Please fix the issues above before testing")
            print("[ERROR] Re-run this validation after making changes")

def main():
    print("[START] Starting Healing-bot Prometheus Configuration Validation...")
    validator = PrometheusConfigValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()
