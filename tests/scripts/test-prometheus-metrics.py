#!/usr/bin/env python3
"""
Test script to validate Prometheus metrics when services are running
Run this after: docker-compose up -d
"""

import requests
import time
import json
from datetime import datetime

class PrometheusMetricsTester:
    def __init__(self):
        self.base_url = "http://localhost"
        self.services = {
            "model": {"port": 8080, "name": "Model API", "metrics_path": "/metrics"},
            "network-analyzer": {"port": 8000, "name": "Network Analyzer", "metrics_path": "/metrics"},
            "incident-bot": {"port": 8000, "name": "Incident Bot", "metrics_path": "/metrics"},
            "server": {"port": 5000, "name": "Monitoring Server", "metrics_path": "/metrics"},
            "dashboard": {"port": 3001, "name": "Dashboard", "metrics_path": "/metrics"},
            "prometheus": {"port": 9090, "name": "Prometheus", "metrics_path": "/api/v1/targets"}
        }
        self.results = {}
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"[TEST] {title}")
        print(f"{'='*60}")
        
    def print_success(self, message):
        print(f"[SUCCESS] {message}")
        
    def print_error(self, message):
        print(f"[ERROR] {message}")
        
    def print_warning(self, message):
        print(f"[WARNING] {message}")
        
    def print_info(self, message):
        print(f"[INFO] {message}")
        
    def test_service_health(self, service_name, port):
        """Test if a service is running and healthy"""
        try:
            url = f"{self.base_url}:{port}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.print_success(f"{service_name} is running on port {port}")
                return True
            else:
                self.print_error(f"{service_name} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"{service_name} is not accessible: {e}")
            return False
    
    def test_metrics_endpoint(self, service_name, port, metrics_path):
        """Test if metrics endpoint is working and contains healing-bot metrics"""
        try:
            url = f"{self.base_url}:{port}{metrics_path}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                metrics_content = response.text
                
                # Count total metrics
                metric_lines = [line for line in metrics_content.split('\n') if line and not line.startswith('#')]
                self.print_success(f"{service_name} metrics endpoint working ({len(metric_lines)} metrics)")
                
                # Check for specific healing-bot metrics
                healing_metrics = []
                for line in metrics_content.split('\n'):
                    if any(keyword in line for keyword in ['ddos_', 'incident_', 'attack_', 'ip_', 'dashboard_', 'geographic_', 'ml_', 'auto_']):
                        if not line.startswith('#'):
                            metric_name = line.split()[0]
                            healing_metrics.append(metric_name)
                
                if healing_metrics:
                    self.print_success(f"Found {len(healing_metrics)} healing-bot specific metrics")
                    for metric in healing_metrics[:5]:  # Show first 5
                        self.print_info(f"  - {metric}")
                    if len(healing_metrics) > 5:
                        self.print_info(f"  ... and {len(healing_metrics) - 5} more")
                    return True, healing_metrics
                else:
                    self.print_warning(f"No healing-bot specific metrics found in {service_name}")
                    return True, []
            else:
                self.print_error(f"{service_name} metrics endpoint returned status {response.status_code}")
                return False, []
        except requests.exceptions.RequestException as e:
            self.print_error(f"{service_name} metrics endpoint not accessible: {e}")
            return False, []
    
    def test_prometheus_targets(self):
        """Test Prometheus targets configuration"""
        try:
            url = f"{self.base_url}:9090/api/v1/targets"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                targets = data.get('data', {}).get('activeTargets', [])
                
                self.print_success(f"Prometheus targets API accessible")
                self.print_info(f"Found {len(targets)} active targets")
                
                # Check for healing-bot targets
                healing_targets = []
                for target in targets:
                    job_name = target.get('labels', {}).get('job', '')
                    if 'healing-bot' in job_name or job_name == 'prometheus':
                        healing_targets.append(target)
                        status = target.get('health', 'unknown')
                        last_scrape = target.get('lastScrape', 'never')
                        scrape_duration = target.get('lastScrapeDuration', 'unknown')
                        self.print_info(f"  - {job_name}: {status} (last: {last_scrape}, duration: {scrape_duration})")
                
                if healing_targets:
                    self.print_success(f"Found {len(healing_targets)} healing-bot targets in Prometheus")
                    return True, healing_targets
                else:
                    self.print_warning("No healing-bot targets found in Prometheus")
                    return False, []
            else:
                self.print_error(f"Prometheus API returned status {response.status_code}")
                return False, []
        except requests.exceptions.RequestException as e:
            self.print_error(f"Prometheus API not accessible: {e}")
            return False, []
    
    def test_prometheus_metrics_query(self):
        """Test querying specific metrics from Prometheus"""
        try:
            # Test querying healing-bot metrics
            test_queries = [
                "ddos_detections_total",
                "incident_alerts_total", 
                "attack_detections_total",
                "ip_blocks_total",
                "dashboard_connections_total",
                "ml_model_accuracy",
                "geographic_attacks_total"
            ]
            
            found_metrics = []
            for query in test_queries:
                url = f"{self.base_url}:9090/api/v1/query"
                params = {'query': query}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'success' and data.get('data', {}).get('result'):
                        found_metrics.append(query)
                        self.print_success(f"Metric '{query}' found in Prometheus")
                    else:
                        self.print_warning(f"Metric '{query}' not found in Prometheus")
                else:
                    self.print_error(f"Failed to query metric '{query}': {response.status_code}")
            
            if found_metrics:
                self.print_success(f"Found {len(found_metrics)} healing-bot metrics in Prometheus")
                return True, found_metrics
            else:
                self.print_warning("No healing-bot metrics found in Prometheus")
                return False, []
                
        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to query Prometheus metrics: {e}")
            return False, []
    
    def test_grafana_access(self):
        """Test if Grafana is accessible"""
        try:
            url = f"{self.base_url}:3000"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                self.print_success("Grafana is accessible at http://localhost:3000")
                return True
            else:
                self.print_error(f"Grafana returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.print_error(f"Grafana not accessible: {e}")
            return False
    
    def generate_metrics_summary(self, all_healing_metrics):
        """Generate a summary of all found metrics"""
        self.print_header("METRICS SUMMARY")
        
        if not all_healing_metrics:
            self.print_warning("No healing-bot metrics found")
            return
        
        # Categorize metrics
        categories = {
            "DDoS Detection": [],
            "Incident Response": [],
            "Network Analysis": [],
            "IP Management": [],
            "Dashboard": [],
            "Geographic": [],
            "ML Model": [],
            "Other": []
        }
        
        for metric in all_healing_metrics:
            if 'ddos_' in metric:
                categories["DDoS Detection"].append(metric)
            elif 'incident_' in metric:
                categories["Incident Response"].append(metric)
            elif 'attack_' in metric:
                categories["Network Analysis"].append(metric)
            elif 'ip_' in metric:
                categories["IP Management"].append(metric)
            elif 'dashboard_' in metric:
                categories["Dashboard"].append(metric)
            elif 'geographic_' in metric:
                categories["Geographic"].append(metric)
            elif 'ml_' in metric:
                categories["ML Model"].append(metric)
            else:
                categories["Other"].append(metric)
        
        for category, metrics in categories.items():
            if metrics:
                self.print_info(f"{category}: {len(metrics)} metrics")
                for metric in metrics[:3]:  # Show first 3
                    self.print_info(f"  - {metric}")
                if len(metrics) > 3:
                    self.print_info(f"  ... and {len(metrics) - 3} more")
    
    def generate_test_report(self):
        """Generate a comprehensive test report"""
        self.print_header("TEST REPORT SUMMARY")
        
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
    
    def run_complete_test(self):
        """Run the complete Prometheus metrics test"""
        self.print_header("HEALING-BOT PROMETHEUS METRICS TEST")
        print(f"[INFO] Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Service Health Checks
        self.print_header("Testing Service Health")
        service_results = {}
        for service, config in self.services.items():
            if service == "prometheus":
                continue  # Test Prometheus separately
            health = self.test_service_health(config['name'], config['port'])
            service_results[service] = health
        
        self.results['service_health'] = {
            'success': all(service_results.values()),
            'details': f"Services healthy: {sum(service_results.values())}/{len(service_results)}"
        }
        
        # Test 2: Metrics Endpoints
        self.print_header("Testing Metrics Endpoints")
        metrics_results = {}
        all_healing_metrics = []
        
        for service, config in self.services.items():
            if service == "prometheus":
                continue
            success, healing_metrics = self.test_metrics_endpoint(
                config['name'], config['port'], config['metrics_path']
            )
            metrics_results[service] = success
            if healing_metrics:
                all_healing_metrics.extend(healing_metrics)
        
        self.results['metrics_endpoints'] = {
            'success': all(metrics_results.values()),
            'details': f"Metrics endpoints working: {sum(metrics_results.values())}/{len(metrics_results)}"
        }
        
        # Test 3: Prometheus Targets
        self.print_header("Testing Prometheus Targets")
        prometheus_targets_success, healing_targets = self.test_prometheus_targets()
        self.results['prometheus_targets'] = {
            'success': prometheus_targets_success,
            'details': f"Found {len(healing_targets)} healing-bot targets"
        }
        
        # Test 4: Prometheus Metrics Query
        self.print_header("Testing Prometheus Metrics Query")
        prometheus_metrics_success, found_metrics = self.test_prometheus_metrics_query()
        self.results['prometheus_metrics'] = {
            'success': prometheus_metrics_success,
            'details': f"Found {len(found_metrics)} healing-bot metrics"
        }
        
        # Test 5: Grafana Access
        self.print_header("Testing Grafana Access")
        grafana_success = self.test_grafana_access()
        self.results['grafana_access'] = {
            'success': grafana_success,
            'details': "Grafana accessible" if grafana_success else "Grafana not accessible"
        }
        
        # Generate metrics summary
        self.generate_metrics_summary(all_healing_metrics)
        
        # Generate final report
        self.generate_test_report()
        
        # Final recommendation
        if all(result.get('success', False) for result in self.results.values()):
            self.print_header("ALL TESTS PASSED!")
            print("[SUCCESS] Your Prometheus setup is working perfectly!")
            print("[SUCCESS] All healing-bot services are exposing metrics")
            print("[SUCCESS] Prometheus is successfully scraping all targets")
            print("[SUCCESS] You can now access Grafana at http://localhost:3000")
            print("[SUCCESS] Import the grafana.json dashboard for comprehensive monitoring")
            print("\n[SUCCESS] Your healing-bot monitoring system is fully operational!")
        else:
            self.print_header("SOME TESTS FAILED")
            print("[ERROR] Please check the failed tests above")
            print("[ERROR] Make sure all services are running: docker-compose up -d")
            print("[ERROR] Wait a few minutes for services to fully start")
            print("[ERROR] Check service logs: docker-compose logs [service-name]")

def main():
    print("[START] Starting Healing-bot Prometheus Metrics Test...")
    print("[INFO] Make sure services are running: docker-compose up -d")
    tester = PrometheusMetricsTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()
