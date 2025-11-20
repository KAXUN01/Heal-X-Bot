"""
Google Gemini AI Log Analyzer
Analyzes centralized logs using Google Gemini API to explain WHY and HOW errors occurred
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiLogAnalyzer:
    """
    Uses Google Gemini API to analyze log entries and provide intelligent insights
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if not self.api_key:
            logger.warning("No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
            self.model = None
        else:
            try:
                # Configure the API key
                genai.configure(api_key=self.api_key)
                # Initialize the model
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                logger.info("Gemini client initialized successfully with gemini-2.0-flash-exp")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                # Try with alternative model name
                try:
                    self.model = genai.GenerativeModel("gemini-1.5-flash")
                    logger.info("Gemini client initialized with gemini-1.5-flash (fallback)")
                except Exception as e2:
                    logger.error(f"Failed to initialize Gemini client with fallback model: {e2}")
                    self.model = None
        
        # Use the modern model name
        self.model_name = "gemini-2.0-flash-exp"
        
        # Analysis cache to avoid re-analyzing same issues
        self.analysis_cache = {}
        
    def analyze_error_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single error log entry using Gemini AI
        """
        if not self.api_key or self.api_key == "your_gemini_api_key_here" or len(self.api_key) < 20:
            return {
                'status': 'error',
                'message': 'Gemini API key not configured or invalid',
                'analysis': 'Please set a valid GEMINI_API_KEY in your .env file.\n\n' +
                           'Get your FREE API key:\n' +
                           '1. Visit: https://aistudio.google.com/app/apikey\n' +
                           '2. Click "Create API Key"\n' +
                           '3. Copy the key and add to .env file:\n' +
                           '   GEMINI_API_KEY=your_actual_key_here\n' +
                           '4. Restart the monitoring server\n\n' +
                           'Note: Make sure you\'re signed in with a Google account.',
                'recommendation': 'Configure API key to enable AI-powered log analysis'
            }
        
        if not self.model:
            return {
                'status': 'error',
                'message': 'Gemini model not initialized. Check API key configuration.',
                'analysis': 'Please set a valid GEMINI_API_KEY in your .env file and restart the server.'
            }
        
        # Check cache first
        cache_key = f"{log_entry.get('service', '')}_{log_entry.get('message', '')[:100]}"
        if cache_key in self.analysis_cache:
            logger.info("Returning cached analysis")
            return self.analysis_cache[cache_key]
        
        # Prepare prompt for Gemini
        prompt = self._create_analysis_prompt(log_entry)
        
        try:
            # Call Gemini API
            response = self._call_gemini_api(prompt)
            
            if response.get('status') == 'success':
                # Parse and structure the analysis
                analysis_result = {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'log_entry': log_entry,
                    'analysis': {
                        'why': self._extract_why_section(response['text']),
                        'how': self._extract_how_section(response['text']),
                        'root_cause': self._extract_root_cause(response['text']),
                        'solution': self._extract_solution(response['text']),
                        'prevention': self._extract_prevention(response['text']),
                        'severity': self._determine_severity(log_entry, response['text']),
                        'full_analysis': response['text']
                    }
                }
                
                # Cache the result
                self.analysis_cache[cache_key] = analysis_result
                
                return analysis_result
            else:
                return response
        
        except Exception as e:
            logger.error(f"Error analyzing log with Gemini: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'analysis': 'Failed to analyze log entry'
            }
    
    def analyze_multiple_logs(self, log_entries: List[Dict[str, Any]], 
                            limit: int = 10) -> Dict[str, Any]:
        """
        Analyze multiple related log entries to find patterns
        """
        if not self.api_key:
            return {
                'status': 'error',
                'message': 'Gemini API key not configured'
            }
        
        if not self.model:
            return {
                'status': 'error',
                'message': 'Gemini model not initialized. Check API key configuration.'
            }
        
        # Limit number of logs to analyze
        logs_to_analyze = log_entries[:limit]
        
        # Create prompt for pattern analysis
        prompt = self._create_pattern_analysis_prompt(logs_to_analyze)
        
        try:
            response = self._call_gemini_api(prompt)
            
            if response.get('status') == 'success':
                return {
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'logs_analyzed': len(logs_to_analyze),
                    'pattern_analysis': {
                        'common_issues': self._extract_common_issues(response['text']),
                        'timeline': self._extract_timeline(response['text']),
                        'correlation': self._extract_correlation(response['text']),
                        'recommendations': self._extract_recommendations(response['text']),
                        'full_analysis': response['text']
                    }
                }
            else:
                return response
        
        except Exception as e:
            logger.error(f"Error analyzing multiple logs: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def analyze_cloud_fault(self, fault: Dict[str, Any], 
                           container_logs: List[str] = None,
                           system_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze cloud-specific faults (service crashes, resource exhaustion, network issues)
        
        Args:
            fault: Fault information dictionary
            container_logs: Optional container logs
            system_metrics: Optional system metrics
            
        Returns:
            AI analysis of the fault
        """
        if not self.api_key or not self.model:
            return {
                'status': 'error',
                'message': 'Gemini API key not configured'
            }
        
        fault_type = fault.get('type', 'unknown')
        service = fault.get('service', 'unknown')
        
        # Create specialized prompt based on fault type
        if fault_type == 'service_crash':
            prompt = self._create_service_crash_prompt(fault, container_logs, system_metrics)
        elif fault_type in ['cpu_exhaustion', 'memory_exhaustion', 'disk_full']:
            prompt = self._create_resource_exhaustion_prompt(fault, system_metrics)
        elif fault_type == 'network_issue':
            prompt = self._create_network_issue_prompt(fault, system_metrics)
        else:
            prompt = self._create_generic_fault_prompt(fault)
        
        try:
            response = self._call_gemini_api(prompt)
            
            if response.get('status') == 'success':
                return {
                    'status': 'success',
                    'fault_type': fault_type,
                    'service': service,
                    'timestamp': datetime.now().isoformat(),
                    'analysis': {
                        'root_cause': self._extract_root_cause(response['text']),
                        'why': self._extract_why_section(response['text']),
                        'solution': self._extract_solution(response['text']),
                        'prevention': self._extract_prevention(response['text']),
                        'confidence': self._estimate_confidence(response['text']),
                        'full_analysis': response['text']
                    }
                }
            else:
                return response
        except Exception as e:
            logger.error(f"Error analyzing cloud fault: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _create_service_crash_prompt(self, fault: Dict[str, Any], 
                                     container_logs: List[str] = None,
                                     system_metrics: Dict[str, Any] = None) -> str:
        """Create prompt for service crash analysis"""
        service = fault.get('service', 'unknown')
        status = fault.get('status', 'unknown')
        restart_count = fault.get('restart_count', 0)
        
        logs_summary = "No logs available"
        if container_logs:
            recent_logs = '\n'.join(container_logs[-10:])
            logs_summary = f"Recent logs:\n{recent_logs}"
        
        metrics_summary = "No metrics available"
        if system_metrics:
            cpu = system_metrics.get('cpu', {}).get('cpu_percent', 0)
            memory = system_metrics.get('memory', {}).get('memory_percent', 0)
            metrics_summary = f"CPU: {cpu}%, Memory: {memory}%"
        
        return f"""
You are an expert DevOps engineer analyzing a Docker container crash in a cloud environment.

FAULT DETAILS:
- Service: {service}
- Status: {status}
- Restart Count: {restart_count}
- Timestamp: {fault.get('timestamp', '')}

SYSTEM METRICS:
{metrics_summary}

CONTAINER LOGS:
{logs_summary}

Analyze this service crash and provide:

🔍 ROOT CAUSE:
[Identify the most likely cause of the crash - OOM kill, application error, resource exhaustion, etc.]

💡 IMMEDIATE FIX:
[2-3 concrete steps to recover the service]

🛡️ PREVENTION:
[How to prevent this from happening again]

CONFIDENCE: [Rate your confidence 0-100%]

Be specific and actionable. Focus on Docker container recovery.
"""
    
    def _create_resource_exhaustion_prompt(self, fault: Dict[str, Any],
                                           system_metrics: Dict[str, Any] = None) -> str:
        """Create prompt for resource exhaustion analysis"""
        fault_type = fault.get('type', 'unknown')
        value = fault.get('value', 0)
        threshold = fault.get('threshold', 0)
        
        metrics_summary = "No detailed metrics available"
        if system_metrics:
            if fault_type == 'cpu_exhaustion':
                cpu = system_metrics.get('cpu', {})
                metrics_summary = f"CPU Usage: {cpu.get('cpu_percent', 0)}%\nCPU Cores: {cpu.get('cpu_count', 0)}"
            elif fault_type == 'memory_exhaustion':
                memory = system_metrics.get('memory', {})
                metrics_summary = f"Memory Usage: {memory.get('memory_percent', 0)}%\nAvailable: {memory.get('memory_available_gb', 0)} GB"
            elif fault_type == 'disk_full':
                disk = system_metrics.get('disk', {})
                metrics_summary = f"Disk Usage: {disk.get('disk_percent', 0)}%\nFree Space: {disk.get('disk_free_gb', 0)} GB"
        
        return f"""
You are an expert system administrator analyzing resource exhaustion in a cloud environment.

FAULT TYPE: {fault_type}
Current Usage: {value}%
Threshold: {threshold}%

SYSTEM METRICS:
{metrics_summary}

Analyze this resource exhaustion and provide:

🔍 ROOT CAUSE:
[Why is this resource exhausted? Identify the cause - memory leak, too many processes, disk full, etc.]

💡 IMMEDIATE FIX:
[2-3 concrete steps to free up resources immediately]

🛡️ PREVENTION:
[How to prevent resource exhaustion in the future]

CONFIDENCE: [Rate your confidence 0-100%]

Be specific and actionable. Focus on immediate recovery.
"""
    
    def _create_network_issue_prompt(self, fault: Dict[str, Any],
                                     system_metrics: Dict[str, Any] = None) -> str:
        """Create prompt for network issue analysis"""
        service = fault.get('service', 'unknown')
        port = fault.get('port', 0)
        
        return f"""
You are an expert network engineer analyzing connectivity issues in a cloud environment.

NETWORK FAULT:
- Service: {service}
- Port: {port}
- Issue: Service not reachable

Analyze this network connectivity issue and provide:

🔍 ROOT CAUSE:
[Why is the service not reachable? Container down, firewall blocking, port conflict, etc.]

💡 IMMEDIATE FIX:
[2-3 concrete steps to restore connectivity]

🛡️ PREVENTION:
[How to prevent network issues in the future]

CONFIDENCE: [Rate your confidence 0-100%]

Be specific and actionable. Focus on Docker networking.
"""
    
    def _create_generic_fault_prompt(self, fault: Dict[str, Any]) -> str:
        """Create prompt for generic fault analysis"""
        return f"""
You are an expert system administrator analyzing a system fault.

FAULT DETAILS:
{json.dumps(fault, indent=2)}

Analyze this fault and provide:

🔍 ROOT CAUSE:
[Identify the root cause]

💡 IMMEDIATE FIX:
[2-3 concrete steps to resolve]

🛡️ PREVENTION:
[How to prevent this in the future]

CONFIDENCE: [Rate your confidence 0-100%]
"""
    
    def _estimate_confidence(self, analysis_text: str) -> float:
        """Estimate confidence from analysis text"""
        # Look for confidence percentage in text
        import re
        confidence_match = re.search(r'CONFIDENCE:\s*(\d+)%', analysis_text, re.IGNORECASE)
        if confidence_match:
            return float(confidence_match.group(1)) / 100.0
        
        # Default confidence based on analysis quality
        if len(analysis_text) > 200:
            return 0.75
        return 0.5
    
    def analyze_service_health(self, service_name: str, 
                              logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze overall health of a specific service based on its logs
        """
        if not self.api_key:
            return {
                'status': 'error',
                'message': 'Gemini API key not configured'
            }
        
        if not self.model:
            return {
                'status': 'error',
                'message': 'Gemini model not initialized. Check API key configuration.'
            }
        
        prompt = f"""
You are an expert system administrator and DevOps engineer analyzing service health.

SERVICE: {service_name}
NUMBER OF LOG ENTRIES: {len(logs)}

RECENT LOGS:
{self._format_logs_for_analysis(logs[:20])}

Please provide a comprehensive health analysis including:

1. OVERALL HEALTH STATUS: (Healthy / Warning / Critical)
2. KEY ISSUES IDENTIFIED: List the main problems
3. PERFORMANCE INDICATORS: What the logs tell us about performance
4. STABILITY ASSESSMENT: Is the service stable or experiencing issues?
5. ACTIONABLE RECOMMENDATIONS: What should be done immediately
6. LONG-TERM IMPROVEMENTS: Suggestions for preventing future issues

Provide a detailed but concise analysis.
"""
        
        try:
            response = self._call_gemini_api(prompt)
            
            if response.get('status') == 'success':
                return {
                    'status': 'success',
                    'service': service_name,
                    'logs_analyzed': len(logs),
                    'health_analysis': {
                        'overall_status': self._extract_health_status(response['text']),
                        'key_issues': self._extract_key_issues(response['text']),
                        'recommendations': self._extract_recommendations(response['text']),
                        'full_analysis': response['text']
                    }
                }
            else:
                return response
        
        except Exception as e:
            logger.error(f"Error analyzing service health: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _create_analysis_prompt(self, log_entry: Dict[str, Any]) -> str:
        """
        Create a concise prompt for Gemini to analyze a log entry
        """
        service = log_entry.get('service', 'Unknown Service')
        message = log_entry.get('message', '')
        timestamp = log_entry.get('timestamp', '')
        source_file = log_entry.get('source_file', '')
        
        prompt = f"""
You are an expert system administrator analyzing system logs. Provide a CONCISE analysis (3-4 sentences per section).

Service: {service}
Timestamp: {timestamp}
Log Message: {message}

Provide a brief analysis in this format:

🔍 WHAT HAPPENED:
[2-3 sentences explaining the root cause and what triggered this]

💡 QUICK FIX:
[2-3 concrete steps to resolve this immediately]

🛡️ PREVENTION:
[1-2 key recommendations to prevent recurrence]

Keep it short, actionable, and easy to understand. No lengthy explanations.
"""
        return prompt
    
    def _create_pattern_analysis_prompt(self, log_entries: List[Dict[str, Any]]) -> str:
        """
        Create prompt for analyzing patterns across multiple logs
        """
        logs_formatted = self._format_logs_for_analysis(log_entries)
        
        prompt = f"""
You are an expert system administrator analyzing system logs for patterns and correlations.

Analyze these {len(log_entries)} log entries:

{logs_formatted}

Please identify:

1. COMMON ISSUES:
   - What errors appear most frequently?
   - Are there recurring patterns?

2. TIMELINE:
   - How did issues evolve over time?
   - Is there a cascade effect?

3. CORRELATION:
   - Are certain errors related?
   - Do issues in one service trigger issues in another?

4. RECOMMENDATIONS:
   - What should be fixed first (prioritized)?
   - What preventive measures are needed?

Provide insights that help understand the overall system health and issues.
"""
        return prompt
    
    def _format_logs_for_analysis(self, logs: List[Dict[str, Any]]) -> str:
        """
        Format log entries for Gemini analysis
        """
        formatted = []
        for i, log in enumerate(logs, 1):
            formatted.append(f"""
Log #{i}:
  Service: {log.get('service', 'Unknown')}
  Time: {log.get('timestamp', '')}
  Message: {log.get('message', '')[:200]}
---""")
        return '\n'.join(formatted)
    
    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Google Gemini API with the prompt using the modern SDK
        """
        if not self.model:
            return {
                'status': 'error',
                'message': 'Gemini client not initialized. Check API key configuration.'
            }
        
        try:
            # Call Gemini using the modern SDK
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return {
                    'status': 'success',
                    'text': response.text
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No response from Gemini API'
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API call failed: {error_msg}")
            
            # Provide helpful error messages
            if 'API key' in error_msg or 'authentication' in error_msg.lower() or '40' in error_msg or '401' in error_msg or '403' in error_msg:
                return {
                    'status': 'error',
                    'message': 'Invalid or Expired API Key',
                    'analysis': ('⚠️  Your Gemini API key is not working.\n\n' +
                               '🔑 HOW TO FIX (Takes 2 minutes):\n\n' +
                               '1. Visit: https://aistudio.google.com/app/apikey\n' +
                               '2. Sign in with your Google account\n' +
                               '3. Click "Create API Key"\n' +
                               '4. Copy the new key (starts with AIza...)\n' +
                               '5. Edit .env file:\n' +
                               '   GEMINI_API_KEY=your_new_key_here\n' +
                               '6. Restart monitoring server:\n' +
                               '   lsof -ti:5000 | xargs kill -9\n' +
                               '   cd monitoring/server && python app.py &\n\n' +
                               '📖 Full instructions: GEMINI_API_KEY_SETUP.md\n\n' +
                               '💡 NOTE: Your system works perfectly without AI.\n' +
                               '   This only affects the AI explanation feature.'),
                    'recommendation': 'Get a new FREE API key from Google AI Studio'
                }
            
            return {
                'status': 'error',
                'message': error_msg
            }
    
    # Helper methods to extract sections from Gemini's response
    
    def _extract_why_section(self, text: str) -> str:
        """Extract WHAT HAPPENED section from analysis"""
        return self._extract_section(text, "WHAT HAPPENED", "QUICK FIX")
    
    def _extract_how_section(self, text: str) -> str:
        """Extract HOW section from analysis (legacy support)"""
        return self._extract_section(text, "WHAT HAPPENED", "QUICK FIX")
    
    def _extract_root_cause(self, text: str) -> str:
        """Extract root cause from analysis"""
        return self._extract_section(text, "WHAT HAPPENED", "QUICK FIX")
    
    def _extract_solution(self, text: str) -> str:
        """Extract solution from analysis"""
        return self._extract_section(text, "QUICK FIX", "PREVENTION")
    
    def _extract_prevention(self, text: str) -> str:
        """Extract prevention measures from analysis"""
        # Get everything after PREVENTION marker
        prevention = self._extract_section(text, "PREVENTION", "END_OF_ANALYSIS")
        if not prevention:
            # Try alternate extraction - get last section
            parts = text.split("🛡️")
            if len(parts) > 1:
                prevention = parts[-1].strip()
        return prevention
    
    def _extract_common_issues(self, text: str) -> str:
        """Extract common issues from pattern analysis"""
        return self._extract_section(text, "COMMON ISSUES", "TIMELINE")
    
    def _extract_timeline(self, text: str) -> str:
        """Extract timeline from pattern analysis"""
        return self._extract_section(text, "TIMELINE", "CORRELATION")
    
    def _extract_correlation(self, text: str) -> str:
        """Extract correlation from pattern analysis"""
        return self._extract_section(text, "CORRELATION", "RECOMMENDATIONS")
    
    def _extract_recommendations(self, text: str) -> str:
        """Extract recommendations"""
        # Try multiple possible headers
        for header in ["RECOMMENDATIONS", "ACTIONABLE RECOMMENDATIONS", "LONG-TERM"]:
            result = self._extract_section(text, header, "END_OF_TEXT_MARKER_XYZ")
            if result and result != "Not found in analysis":
                return result
        return self._extract_after_keyword(text, "recommend")
    
    def _extract_health_status(self, text: str) -> str:
        """Extract health status"""
        return self._extract_section(text, "OVERALL HEALTH STATUS", "KEY ISSUES")
    
    def _extract_key_issues(self, text: str) -> str:
        """Extract key issues"""
        return self._extract_section(text, "KEY ISSUES", "PERFORMANCE")
    
    def _extract_section(self, text: str, start_marker: str, end_marker: str) -> str:
        """
        Extract a section between two markers
        """
        try:
            start_idx = text.upper().find(start_marker.upper())
            if start_idx == -1:
                return "Not found in analysis"
            
            # Find where content starts (after the header)
            content_start = text.find(':', start_idx) + 1
            if content_start == 0:
                content_start = start_idx + len(start_marker)
            
            # Find end marker
            end_idx = text.upper().find(end_marker.upper(), content_start)
            if end_idx == -1:
                # If no end marker, take rest of text up to 500 chars
                return text[content_start:content_start + 500].strip()
            
            return text[content_start:end_idx].strip()
        
        except Exception as e:
            logger.error(f"Error extracting section: {e}")
            return "Error extracting information"
    
    def _extract_after_keyword(self, text: str, keyword: str) -> str:
        """Extract text after a keyword"""
        try:
            idx = text.lower().find(keyword.lower())
            if idx != -1:
                return text[idx:idx + 300].strip()
            return "Not found"
        except:
            return "Error extracting"
    
    def _determine_severity(self, log_entry: Dict[str, Any], analysis_text: str) -> str:
        """
        Determine severity based on log entry and analysis
        """
        message = log_entry.get('message', '').lower()
        text_lower = analysis_text.lower()
        
        # Check for severity indicators
        if any(word in text_lower for word in ['critical', 'severe', 'fatal', 'emergency']):
            return 'CRITICAL'
        elif any(word in text_lower for word in ['error', 'failure', 'failed']):
            return 'HIGH'
        elif any(word in text_lower for word in ['warning', 'warn', 'degraded']):
            return 'MEDIUM'
        else:
            return 'LOW'


# Global analyzer instance
gemini_analyzer = None


def initialize_gemini_analyzer(api_key: str = None):
    """Initialize the Gemini log analyzer"""
    global gemini_analyzer
    gemini_analyzer = GeminiLogAnalyzer(api_key=api_key)
    logger.info("Gemini log analyzer initialized")
    return gemini_analyzer


if __name__ == "__main__":
    # Test the analyzer
    analyzer = initialize_gemini_analyzer()
    
    # Test log entry
    test_log = {
        'timestamp': '2025-10-28T14:30:45.123456',
        'service': 'database',
        'source_file': '/var/log/mysql/error.log',
        'message': 'ERROR: Too many connections (max_connections=151)'
    }
    
    print("Analyzing log entry...")
    result = analyzer.analyze_error_log(test_log)
    
    if result['status'] == 'success':
        print("\n" + "="*60)
        print("GEMINI AI ANALYSIS")
        print("="*60)
        print(f"\nWHY: {result['analysis']['why']}")
        print(f"\nHOW: {result['analysis']['how']}")
        print(f"\nSOLUTION: {result['analysis']['solution']}")
        print(f"\nSEVERITY: {result['analysis']['severity']}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

