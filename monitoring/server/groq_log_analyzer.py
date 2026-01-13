"""
Groq AI Log Analyzer
Analyzes centralized logs using Groq API to explain WHY and HOW errors occurred
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqLogAnalyzer:
    """
    Uses Groq API to analyze log entries and provide intelligent insights
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        
        if not self.api_key:
            logger.warning("No Groq API key found. Set GROQ_API_KEY environment variable")
            self.client = None
            self.model_name = None
        else:
            try:
                # Initialize Groq client
                self.client = Groq(api_key=self.api_key)
                # Use llama-3.3-70b-versatile model (better reasoning capabilities)
                # Fallback models: llama-3.1-8b-instant (faster)
                self.model_name = "llama-3.3-70b-versatile"
                logger.info(f"Groq client initialized successfully with {self.model_name}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
                self.model_name = None
        
        # Analysis cache to avoid re-analyzing same issues
        self.analysis_cache = {}
        
    def analyze_error_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single error log entry using Groq AI
        """
        # Try to reload API key from environment if not set
        if not self.api_key or self.api_key == "your_groq_api_key_here" or len(self.api_key) < 20:
            # Reload from environment in case it was added after initialization
            self.api_key = os.getenv('GROQ_API_KEY')
            
            # If we now have a valid API key, try to initialize the client
            if self.api_key and self.api_key != "your_groq_api_key_here" and len(self.api_key) >= 20:
                try:
                    self.client = Groq(api_key=self.api_key)
                    self.model_name = "llama-3.3-70b-versatile"
                    logger.info(f"Groq client initialized with {self.model_name} after reloading API key")
                except Exception as e:
                    logger.error(f"Failed to initialize Groq client after reloading API key: {e}")
        
        # Check again after reload attempt
        if not self.api_key or self.api_key == "your_groq_api_key_here" or len(self.api_key) < 20:
            api_key_info = f"API key length: {len(self.api_key) if self.api_key else 0} characters"
            if self.api_key and self.api_key != "your_groq_api_key_here":
                api_key_info += f" (starts with: {self.api_key[:10]}...)"
            return {
                'status': 'error',
                'message': 'Groq API key not configured or invalid',
                'analysis': f'Please set a valid GROQ_API_KEY in your .env file.\n\n{api_key_info}\n\n' +
                           'Get your API key:\n' +
                           '1. Visit: https://console.groq.com/keys\n' +
                           '2. Sign in or create an account\n' +
                           '3. Click "Create API Key"\n' +
                           '4. Copy the key and add to .env file:\n' +
                           '   GROQ_API_KEY=your_actual_key_here\n' +
                           '5. Restart the monitoring server\n\n' +
                           'Note: Make sure you have a valid Groq account.',
                'recommendation': 'Configure API key to enable AI-powered log analysis'
            }
        
        if not self.client:
            # Provide more helpful error message
            error_msg = 'Groq client not initialized. '
            if self.api_key:
                error_msg += f'API key is set ({len(self.api_key)} chars), but client initialization failed.\n\n'
                error_msg += 'Possible causes:\n'
                error_msg += '1. API key is invalid or expired\n'
                error_msg += '2. No internet connectivity\n'
                error_msg += '3. API key doesn\'t have proper permissions\n\n'
                error_msg += 'Please check your API key and restart the server.'
            else:
                error_msg += 'Please set a valid GROQ_API_KEY in your .env file and restart the server.'
            
            return {
                'status': 'error',
                'message': 'Groq client not initialized. Check API key configuration.',
                'analysis': error_msg
            }
        
        # Check cache first
        cache_key = f"{log_entry.get('service', '')}_{log_entry.get('message', '')[:100]}"
        if cache_key in self.analysis_cache:
            logger.info("Returning cached analysis")
            return self.analysis_cache[cache_key]
        
        # Prepare prompt for Groq
        prompt = self._create_analysis_prompt(log_entry)
        
        try:
            # Call Groq API
            response = self._call_groq_api(prompt)
            
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
            logger.error(f"Error analyzing log with Groq: {e}")
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
                'message': 'Groq API key not configured'
            }
        
        if not self.client:
            return {
                'status': 'error',
                'message': 'Groq client not initialized. Check API key configuration.'
            }
        
        # Limit number of logs to analyze
        logs_to_analyze = log_entries[:limit]
        
        # Create prompt for pattern analysis
        prompt = self._create_pattern_analysis_prompt(logs_to_analyze)
        
        try:
            response = self._call_groq_api(prompt)
            
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
        if not self.api_key or not self.client:
            return {
                'status': 'error',
                'message': 'Groq API key not configured'
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
            response = self._call_groq_api(prompt)
            
            if response.get('status') == 'success':
                return {
                    'status': 'success',
                    'fault_type': fault_type,
                    'service': service,
                    'timestamp': datetime.now().isoformat(),
                    'analysis': {
                        'root_cause': self._extract_root_cause(response['text']),
                        # 'why' field removed to prevent duplication in UI
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
[Identify the most likely cause - OOM kill, application error, etc.]
 
💡 IMMEDIATE FIX:
[1-2 concrete steps to recover]
 
🛡️ PREVENTION:
[1 sentence on how to prevent this]
 
CONFIDENCE: [Rate your confidence 0-100%]
 
Keep it EXTREMELY concise (max 2 sentences per section).
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
[Identify the cause - memory leak, etc.]
 
💡 IMMEDIATE FIX:
[1-2 concrete steps to free up resources]
 
🛡️ PREVENTION:
[1 sentence on prevention]
 
CONFIDENCE: [Rate your confidence 0-100%]
 
Keep it EXTREMELY concise (max 2 sentences per section).
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
[Why is the service not reachable?]
 
💡 IMMEDIATE FIX:
[1-2 concrete steps to restore connectivity]
 
🛡️ PREVENTION:
[1 sentence on prevention]
 
CONFIDENCE: [Rate your confidence 0-100%]
 
Keep it EXTREMELY concise (max 2 sentences per section).
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
[1-2 concrete steps to resolve]
 
🛡️ PREVENTION:
[1 sentence on prevention]
 
CONFIDENCE: [Rate your confidence 0-100%]

Keep it EXTREMELY concise (max 2 sentences per section).
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
                'message': 'Groq API key not configured'
            }
        
        if not self.client:
            return {
                'status': 'error',
                'message': 'Groq client not initialized. Check API key configuration.'
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
            response = self._call_groq_api(prompt)
            
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
        Create a concise prompt for Groq to analyze a log entry
        """
        service = log_entry.get('service', 'Unknown Service')
        message = log_entry.get('message', '')
        timestamp = log_entry.get('timestamp', '')
        source_file = log_entry.get('source_file', '')
        
        # Truncate message if too long (keep only first 300 chars for faster processing)
        message_short = message[:300] + ('...' if len(message) > 300 else '')
        
        prompt = f"""Analyze this log error. Be BRIEF (max 2 sentences per section):

Service: {service}
Error: {message_short}

Format:
🔍 WHAT HAPPENED: [1-2 sentences]
💡 QUICK FIX: [1-2 steps]
🛡️ PREVENTION: [1 sentence]

Keep it short and actionable."""
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
        Format log entries for Groq analysis
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
    
    def _call_groq_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call Groq API with the prompt using the Groq SDK
        Optimized for speed with timeout and token limits
        """
        if not self.client:
            return {
                'status': 'error',
                'message': 'Groq client not initialized. Check API key configuration.'
            }
        
        try:
            import threading
            import queue
            
            # Use threading with queue for timeout
            result_queue = queue.Queue()
            
            def api_call():
                try:
                    # Attempt 1: Try primary model
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.1,
                            max_tokens=350,
                            top_p=0.7,
                        )
                        result_queue.put(('success', response))
                        return
                    except Exception as first_error:
                        # Attempt 2: Try fallback model if primary is not Mixtral
                        fallback_model = "mixtral-8x7b-32768"
                        if self.model_name == fallback_model:
                            raise first_error
                        
                        logger.warning(f"Primary model {self.model_name} failed: {first_error}. Retrying with fallback {fallback_model}...")
                        
                        response = self.client.chat.completions.create(
                            model=fallback_model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.1,
                            max_tokens=350,
                            top_p=0.7,
                        )
                        # If success, update logs
                        logger.info(f"Fallback to {fallback_model} successful")
                        result_queue.put(('success', response))
                        
                except Exception as e:
                    result_queue.put(('error', e))
            
            # Start API call in a thread
            thread = threading.Thread(target=api_call)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10)  # 10 second timeout for faster feedback
            
            if thread.is_alive():
                # Request timed out
                logger.warning(f"Groq API call ({self.model_name}) timed out after 10 seconds")
                return {
                    'status': 'error',
                    'message': 'Analysis timed out. The AI model is taking longer than expected. Please try again.'
                }
            
            # Get result from queue
            try:
                result_type, result = result_queue.get_nowait()
                if result_type == 'error':
                    raise result
                response = result
            except queue.Empty:
                return {
                    'status': 'error',
                    'message': 'No response received from Groq API'
                }
            
            if response and response.choices and len(response.choices) > 0:
                text = response.choices[0].message.content
                if text:
                    return {
                        'status': 'success',
                        'text': text
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'No content in Groq API response'
                    }
            else:
                return {
                    'status': 'error',
                    'message': 'No response from Groq API'
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Groq API call failed: {error_msg}")
            
            # Provide helpful error messages
            if 'API key' in error_msg or 'authentication' in error_msg.lower() or '40' in error_msg or '401' in error_msg or '403' in error_msg:
                return {
                    'status': 'error',
                    'message': 'Invalid or Expired API Key',
                    'analysis': ('⚠️  Your Groq API key is not working.\n\n' +
                               '🔑 HOW TO FIX (Takes 2 minutes):\n\n' +
                               '1. Visit: https://console.groq.com/keys\n' +
                               '2. Sign in or create an account\n' +
                               '3. Click "Create API Key"\n' +
                               '4. Copy the new key\n' +
                               '5. Edit .env file:\n' +
                               '   GROQ_API_KEY=your_new_key_here\n' +
                               '6. Restart monitoring server:\n' +
                               '   lsof -ti:5000 | xargs kill -9\n' +
                               '   cd monitoring/server && python app.py &\n\n' +
                               '💡 NOTE: Your system works perfectly without AI.\n' +
                               '   This only affects the AI explanation feature.'),
                    'recommendation': 'Get a new API key from Groq Console'
                }
            
            return {
                'status': 'error',
                'message': error_msg
            }
    
    # Helper methods to extract sections from Groq's response
    
    def _extract_why_section(self, text: str) -> str:
        """Extract WHAT HAPPENED section from analysis"""
        # Map root cause to "why" for compatibility
        return self._extract_root_cause(text)
    
    def _extract_how_section(self, text: str) -> str:
        """Extract HOW section from analysis (legacy support)"""
        return self._extract_section(text, "💡 IMMEDIATE FIX", "IMMEDIATE FIX")
    
    def _extract_root_cause(self, text: str) -> str:
        """Extract root cause from analysis"""
        # Try different variations of the header
        for header in ["🔍 ROOT CAUSE", "ROOT CAUSE", "WHAT HAPPENED", "🔍 WHAT HAPPENED"]:
            content = self._extract_section(text, header, "IMMEDIATE FIX")
            if content and content != "Not found in analysis":
                return content
        return "Not found in analysis"
    
    def _extract_solution(self, text: str) -> str:
        """Extract solution from analysis"""
        for header in ["💡 IMMEDIATE FIX", "IMMEDIATE FIX", "QUICK FIX", "💡 QUICK FIX"]:
            content = self._extract_section(text, header, "PREVENTION")
            if content and content != "Not found in analysis":
                return content
        return "Not found in analysis"
    
    def _extract_prevention(self, text: str) -> str:
        """Extract prevention measures from analysis"""
        # Get everything after PREVENTION marker
        for header in ["🛡️ PREVENTION", "PREVENTION"]:
            content = self._extract_section(text, header, "CONFIDENCE")
            if content and content != "Not found in analysis":
                return content
        
        # Try alternate extraction - get last section
        parts = text.split("🛡️")
        if len(parts) > 1:
            return parts[-1].split("CONFIDENCE")[0].strip()
        return "Not found in analysis"
    
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
groq_analyzer = None


def initialize_groq_analyzer(api_key: str = None):
    """Initialize the Groq log analyzer"""
    global groq_analyzer
    
    # If no API key provided, try to get it from environment
    if not api_key:
        api_key = os.getenv('GROQ_API_KEY')
    
    # Create analyzer with API key
    groq_analyzer = GroqLogAnalyzer(api_key=api_key)
    
    # Log initialization status
    if groq_analyzer.api_key and groq_analyzer.client:
        logger.info(f"Groq log analyzer initialized successfully with model: {groq_analyzer.model_name}")
    elif groq_analyzer.api_key:
        logger.warning(f"Groq log analyzer initialized with API key but client not available (key length: {len(groq_analyzer.api_key)})")
    else:
        logger.warning("Groq log analyzer initialized without API key (AI analysis disabled)")
    
    return groq_analyzer


if __name__ == "__main__":
    # Test the analyzer
    analyzer = initialize_groq_analyzer()
    
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
        print("GROQ AI ANALYSIS")
        print("="*60)
        print(f"\nWHY: {result['analysis']['why']}")
        print(f"\nHOW: {result['analysis']['how']}")
        print(f"\nSOLUTION: {result['analysis']['solution']}")
        print(f"\nSEVERITY: {result['analysis']['severity']}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")

