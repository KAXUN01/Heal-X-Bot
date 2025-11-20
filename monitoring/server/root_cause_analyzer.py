"""
Root Cause Analyzer - Multi-source correlation and root cause identification
Analyzes faults from multiple sources (logs, metrics, container status) to identify root causes
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from container_monitor import ContainerMonitor
from resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)

class RootCauseAnalyzer:
    """Analyze root causes by correlating multiple data sources"""
    
    def __init__(self, gemini_analyzer=None):
        """
        Initialize root cause analyzer
        
        Args:
            gemini_analyzer: Optional Gemini AI analyzer for advanced analysis
        """
        self.container_monitor = ContainerMonitor()
        self.resource_monitor = ResourceMonitor()
        self.gemini_analyzer = gemini_analyzer
        
        logger.info("Root Cause Analyzer initialized")
    
    def analyze_fault(self, fault: Dict[str, Any], 
                     container_logs: List[str] = None,
                     system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a fault to determine root cause
        
        Args:
            fault: Fault information dictionary
            container_logs: Optional container logs
            system_metrics: Optional system metrics
            
        Returns:
            Root cause analysis result
        """
        fault_type = fault.get('type', 'unknown')
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'root_cause': None,
            'confidence': 0.0,
            'correlated_events': [],
            'fault_classification': None,
            'recommended_actions': []
        }
        
        # Analyze based on fault type
        if fault_type == 'service_crash':
            analysis = self._analyze_service_crash(fault, container_logs, system_metrics)
        elif fault_type == 'cpu_exhaustion':
            analysis = self._analyze_cpu_exhaustion(fault, system_metrics)
        elif fault_type == 'memory_exhaustion':
            analysis = self._analyze_memory_exhaustion(fault, system_metrics)
        elif fault_type == 'disk_full':
            analysis = self._analyze_disk_full(fault, system_metrics)
        elif fault_type == 'network_issue':
            analysis = self._analyze_network_issue(fault, system_metrics)
        else:
            analysis['root_cause'] = 'Unknown fault type'
            analysis['confidence'] = 0.1
        
        # Use Gemini AI for advanced analysis if available
        if self.gemini_analyzer and fault.get('details'):
            ai_analysis = self._get_ai_analysis(fault, analysis)
            if ai_analysis:
                analysis['ai_insights'] = ai_analysis
                # Update confidence if AI provides higher confidence
                if ai_analysis.get('confidence', 0) > analysis['confidence']:
                    analysis['confidence'] = ai_analysis.get('confidence', 0)
                    analysis['root_cause'] = ai_analysis.get('root_cause', analysis['root_cause'])
        
        return analysis
    
    def _analyze_service_crash(self, fault: Dict[str, Any], 
                               container_logs: List[str] = None,
                               system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze service crash fault"""
        service = fault.get('service', 'unknown')
        status = fault.get('status', 'unknown')
        restart_count = fault.get('restart_count', 0)
        
        # Get container status
        container_status = self.container_monitor.get_container_status(service)
        
        # Get container logs if available
        logs = container_logs or self.container_monitor.get_container_logs(service, tail=50)
        
        # Analyze logs for error patterns
        error_patterns = self._detect_error_patterns(logs)
        
        # Check resource usage
        resources = system_metrics or self.resource_monitor.get_all_resources()
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'fault_classification': 'service_crash',
            'root_cause': None,
            'confidence': 0.5,
            'correlated_events': [],
            'recommended_actions': []
        }
        
        # Determine root cause based on evidence
        root_causes = []
        
        # Check for OOM (Out of Memory) kills
        if any('OOM' in log or 'out of memory' in log.lower() for log in logs):
            root_causes.append({
                'cause': 'Out of Memory (OOM) kill',
                'confidence': 0.9,
                'evidence': 'OOM kill detected in logs'
            })
            analysis['recommended_actions'].append('Increase container memory limit')
            analysis['recommended_actions'].append('Check for memory leaks')
        
        # Check for resource exhaustion
        if resources.get('memory', {}).get('memory_percent', 0) > 95:
            root_causes.append({
                'cause': 'System memory exhaustion',
                'confidence': 0.8,
                'evidence': f"System memory at {resources['memory']['memory_percent']}%"
            })
            analysis['recommended_actions'].append('Free up system memory')
        
        if resources.get('cpu', {}).get('cpu_percent', 0) > 90:
            root_causes.append({
                'cause': 'High CPU usage',
                'confidence': 0.7,
                'evidence': f"CPU usage at {resources['cpu']['cpu_percent']}%"
            })
            analysis['recommended_actions'].append('Reduce CPU load')
        
        # Check restart count
        if restart_count > 5:
            root_causes.append({
                'cause': 'Repeated crashes (restart loop)',
                'confidence': 0.85,
                'evidence': f"Container restarted {restart_count} times"
            })
            analysis['recommended_actions'].append('Investigate application code')
            analysis['recommended_actions'].append('Check application logs')
        
        # Check for database connection issues
        if any('database' in log.lower() or 'connection' in log.lower() for log in logs[-10:]):
            root_causes.append({
                'cause': 'Database connection failure',
                'confidence': 0.75,
                'evidence': 'Database connection errors in logs'
            })
            analysis['recommended_actions'].append('Check database service status')
            analysis['recommended_actions'].append('Verify database credentials')
        
        # Select highest confidence root cause
        if root_causes:
            best_cause = max(root_causes, key=lambda x: x['confidence'])
            analysis['root_cause'] = best_cause['cause']
            analysis['confidence'] = best_cause['confidence']
            analysis['correlated_events'] = root_causes
        else:
            analysis['root_cause'] = 'Unknown cause - container stopped unexpectedly'
            analysis['confidence'] = 0.3
            analysis['recommended_actions'].append('Check container logs')
            analysis['recommended_actions'].append('Review application configuration')
        
        return analysis
    
    def _analyze_cpu_exhaustion(self, fault: Dict[str, Any], 
                                system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze CPU exhaustion fault"""
        resources = system_metrics or self.resource_monitor.get_all_resources()
        cpu_percent = resources.get('cpu', {}).get('cpu_percent', 0)
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'fault_classification': 'resource_exhaustion',
            'root_cause': 'High CPU usage detected',
            'confidence': 0.9,
            'correlated_events': [],
            'recommended_actions': [
                'Identify CPU-intensive processes',
                'Kill resource-hogging processes',
                'Scale up resources if needed',
                'Optimize application code'
            ]
        }
        
        # Check per-core CPU usage
        cpu_per_core = resources.get('cpu', {}).get('cpu_per_core', [])
        if cpu_per_core:
            max_core = max(cpu_per_core)
            if max_core > 95:
                analysis['root_cause'] = f'Single core saturation (Core at {max_core}%)'
                analysis['recommended_actions'].append('Distribute load across cores')
        
        return analysis
    
    def _analyze_memory_exhaustion(self, fault: Dict[str, Any],
                                   system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze memory exhaustion fault"""
        resources = system_metrics or self.resource_monitor.get_all_resources()
        memory_percent = resources.get('memory', {}).get('memory_percent', 0)
        memory_available = resources.get('memory', {}).get('memory_available_gb', 0)
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'fault_classification': 'resource_exhaustion',
            'root_cause': f'Memory exhaustion ({memory_percent}% used, {memory_available:.2f} GB available)',
            'confidence': 0.9,
            'correlated_events': [],
            'recommended_actions': [
                'Free up memory by killing unnecessary processes',
                'Clear system caches',
                'Restart memory-intensive services',
                'Increase available memory'
            ]
        }
        
        return analysis
    
    def _analyze_disk_full(self, fault: Dict[str, Any],
                           system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze disk full fault"""
        resources = system_metrics or self.resource_monitor.get_all_resources()
        disk_percent = resources.get('disk', {}).get('disk_percent', 0)
        disk_free = resources.get('disk', {}).get('disk_free_gb', 0)
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'fault_classification': 'resource_exhaustion',
            'root_cause': f'Disk space exhausted ({disk_percent}% used, {disk_free:.2f} GB free)',
            'confidence': 0.95,
            'correlated_events': [],
            'recommended_actions': [
                'Clean up old log files',
                'Remove unused Docker images and containers',
                'Clear temporary files',
                'Archive old data',
                'Increase disk space'
            ]
        }
        
        return analysis
    
    def _analyze_network_issue(self, fault: Dict[str, Any],
                              system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze network connectivity issue"""
        service = fault.get('service', 'unknown')
        port = fault.get('port', 0)
        
        analysis = {
            'fault': fault,
            'timestamp': datetime.now().isoformat(),
            'fault_classification': 'network_issue',
            'root_cause': f'Service {service} not reachable on port {port}',
            'confidence': 0.8,
            'correlated_events': [],
            'recommended_actions': [
                f'Check if {service} container is running',
                f'Verify port {port} is not blocked by firewall',
                'Check network connectivity',
                'Restart network services if needed',
                f'Restart {service} container'
            ]
        }
        
        # Check if container is running
        container_status = self.container_monitor.get_container_status(service)
        if not container_status.get('is_running', False):
            analysis['root_cause'] = f'Container {service} is not running'
            analysis['confidence'] = 0.95
            analysis['recommended_actions'].insert(0, f'Start container: docker start {service}')
        
        return analysis
    
    def _detect_error_patterns(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Detect common error patterns in logs"""
        patterns = []
        
        error_keywords = {
            'OOM': 'Out of Memory',
            'connection refused': 'Connection refused',
            'timeout': 'Timeout error',
            'permission denied': 'Permission denied',
            'no space left': 'Disk full',
            'database': 'Database error',
            'network': 'Network error'
        }
        
        for log_line in logs[-20:]:  # Check last 20 lines
            log_lower = log_line.lower()
            for keyword, description in error_keywords.items():
                if keyword in log_lower:
                    patterns.append({
                        'pattern': keyword,
                        'description': description,
                        'log_line': log_line[:200]  # Truncate long lines
                    })
                    break
        
        return patterns
    
    def _get_ai_analysis(self, fault: Dict[str, Any], 
                         current_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get AI-powered analysis using Gemini"""
        if not self.gemini_analyzer:
            return None
        
        try:
            # Create a log entry format for Gemini
            log_entry = {
                'service': fault.get('service', 'unknown'),
                'message': fault.get('message', ''),
                'level': fault.get('severity', 'error').upper(),
                'timestamp': fault.get('timestamp', '')
            }
            
            # Analyze with Gemini
            ai_result = self.gemini_analyzer.analyze_error_log(log_entry)
            
            if ai_result.get('status') == 'success':
                analysis = ai_result.get('analysis', {})
                return {
                    'root_cause': analysis.get('root_cause', current_analysis.get('root_cause')),
                    'confidence': 0.8,  # AI analysis confidence
                    'why': analysis.get('why', ''),
                    'solution': analysis.get('solution', ''),
                    'prevention': analysis.get('prevention', '')
                }
        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}")
        
        return None
    
    def classify_fault(self, fault: Dict[str, Any]) -> str:
        """
        Classify fault type
        
        Returns:
            Fault classification string
        """
        fault_type = fault.get('type', 'unknown')
        
        classifications = {
            'service_crash': 'Container Failure',
            'cpu_exhaustion': 'Resource Exhaustion',
            'memory_exhaustion': 'Resource Exhaustion',
            'disk_full': 'Resource Exhaustion',
            'network_issue': 'Connectivity Issue'
        }
        
        return classifications.get(fault_type, 'Unknown Fault')


# Singleton instance
_root_cause_analyzer_instance = None

def initialize_root_cause_analyzer(gemini_analyzer=None) -> RootCauseAnalyzer:
    """Initialize the root cause analyzer"""
    global _root_cause_analyzer_instance
    
    if _root_cause_analyzer_instance is None:
        _root_cause_analyzer_instance = RootCauseAnalyzer(gemini_analyzer=gemini_analyzer)
        logger.info("Root cause analyzer initialized")
    
    return _root_cause_analyzer_instance

def get_root_cause_analyzer() -> Optional[RootCauseAnalyzer]:
    """Get the root cause analyzer instance"""
    return _root_cause_analyzer_instance

