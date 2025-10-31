"""
Fluent Bit Log Reader
Reads logs collected by Fluent Bit and provides them via API
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FluentBitReader:
    """Reads and manages logs from Fluent Bit"""
    
    def __init__(self, log_file_path: str = '/var/log/fluent-bit/fluent-bit-output.jsonl'):
        """
        Initialize Fluent Bit reader
        
        Args:
            log_file_path: Path to Fluent Bit output JSONL file
        """
        self.log_file_path = Path(log_file_path)
        self.last_position = 0
        self.log_cache = []  # In-memory cache of recent logs
        self.max_cache_size = 10000  # Keep last 10k logs in memory
        
        # Ensure directory exists
        try:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.warning(f"Cannot create directory {self.log_file_path.parent}: Permission denied")
        
        # Load existing logs if file exists
        if self.log_file_path.exists():
            try:
                # Check if file is readable
                if not os.access(str(self.log_file_path), os.R_OK):
                    logger.warning(f"Fluent Bit log file exists but is not readable: {self.log_file_path}")
                else:
                    self._load_existing_logs()
            except Exception as e:
                logger.error(f"Error checking/loading Fluent Bit log file: {e}", exc_info=True)
        else:
            logger.info(f"Fluent Bit log file not found at {self.log_file_path}. Reader initialized - will start reading when file is created.")
    
    def _load_existing_logs(self):
        """Load existing logs from file into cache"""
        try:
            logger.debug(f"Attempting to load logs from: {self.log_file_path}")
            parsed_count = 0
            failed_count = 0
            
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                total_lines = len(lines)
                logger.debug(f"Read {total_lines} lines from file")
                
                # Load last 5000 lines to avoid memory issues
                lines_to_process = lines[-5000:] if len(lines) > 5000 else lines
                
                for line_num, line in enumerate(lines_to_process, 1):
                    if line.strip():
                        try:
                            # Try parsing as JSON first (standard JSON lines format)
                            log_entry = json.loads(line)
                            parsed = self._parse_fluent_bit_entry(log_entry)
                            self.log_cache.append(parsed)
                            parsed_count += 1
                        except json.JSONDecodeError:
                            # Try parsing Fluent Bit default format: tag: [timestamp, {json}]
                            try:
                                parsed = self._parse_fluent_bit_format(line)
                                if parsed:
                                    self.log_cache.append(parsed)
                                    parsed_count += 1
                                else:
                                    failed_count += 1
                            except Exception as parse_error:
                                failed_count += 1
                                if line_num <= 5:  # Log first few failures for debugging
                                    logger.debug(f"Failed to parse line {line_num}: {str(parse_error)[:100]}")
                                continue
                
                self.last_position = f.tell() if hasattr(f, 'tell') else len('\n'.join(lines))
                
            logger.info(f"Loaded {len(self.log_cache)} existing Fluent Bit logs (parsed: {parsed_count}, failed: {failed_count})")
            if failed_count > 0 and parsed_count == 0:
                logger.warning(f"All {failed_count} lines failed to parse. Check log format.")
        except PermissionError as e:
            logger.error(f"Permission denied reading Fluent Bit log file: {self.log_file_path}. Error: {e}")
            logger.error(f"Try: sudo chmod 644 {self.log_file_path} or add user to docker group")
        except Exception as e:
            logger.error(f"Could not load existing Fluent Bit logs: {e}", exc_info=True)
    
    def _parse_fluent_bit_format(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse Fluent Bit default format: tag: [timestamp, {json_object}]
        
        Example: syslog: [1761907632.347229860, {"log":"message","fluent_bit":"true"}]
        """
        try:
            line = line.strip()
            if not line:
                return None
            
            # Check if it's in the format: tag: [timestamp, {...}]
            if ': [' in line:
                parts = line.split(': [', 1)
                if len(parts) == 2:
                    tag = parts[0].strip()
                    json_part = '[' + parts[1]
                    
                    # Parse the JSON array
                    data = json.loads(json_part)
                    if len(data) >= 2:
                        timestamp_val = data[0]
                        json_obj = data[1]
                        
                        # Convert timestamp if it's a number
                        if isinstance(timestamp_val, (int, float)):
                            timestamp = datetime.fromtimestamp(timestamp_val).isoformat()
                        else:
                            timestamp = str(timestamp_val)
                        
                        # Add tag to the JSON object
                        json_obj['tag'] = tag
                        json_obj['time'] = timestamp
                        
                        return self._parse_fluent_bit_entry(json_obj)
            
            return None
        except Exception as e:
            logger.debug(f"Error parsing Fluent Bit format line: {e}")
            return None
    
    def _parse_fluent_bit_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Fluent Bit log entry into standardized format
        
        Fluent Bit entries typically have:
        - @timestamp or time
        - tag (source tag)
        - log (original message)
        - Additional parsed fields
        """
        # Extract timestamp
        timestamp = entry.get('@timestamp') or entry.get('time') or datetime.now().isoformat()
        
        # Extract service/source from tag
        tag = entry.get('tag', 'unknown')
        if isinstance(tag, list) and len(tag) > 0:
            tag = tag[0]
        
        # Determine service name from tag
        service = tag.split('.')[0] if '.' in tag else tag
        
        # Extract message
        message = entry.get('log') or entry.get('message') or entry.get('msg') or str(entry)
        if isinstance(message, dict):
            message = json.dumps(message)
        
        # Extract log level
        level = entry.get('level') or entry.get('severity') or self._detect_log_level(str(message))
        
        # Extract additional fields
        source_file = entry.get('source_file') or entry.get('_PATH') or tag
        
        return {
            'timestamp': timestamp,
            'service': service,
            'source': 'fluent-bit',
            'source_file': source_file,
            'tag': tag,
            'message': str(message),
            'level': level.upper(),
            'raw': entry  # Keep raw entry for debugging
        }
    
    def _detect_log_level(self, message: str) -> str:
        """Detect log level from message content"""
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ['critical', 'fatal', 'emergency', 'panic']):
            return 'CRITICAL'
        elif any(kw in msg_lower for kw in ['error', 'err', 'failed', 'failure']):
            return 'ERROR'
        elif any(kw in msg_lower for kw in ['warn', 'warning', 'caution']):
            return 'WARNING'
        elif any(kw in msg_lower for kw in ['debug', 'trace']):
            return 'DEBUG'
        else:
            return 'INFO'
    
    def refresh_logs(self) -> int:
        """
        Read new logs from Fluent Bit output file
        
        Returns:
            Number of new logs read
        """
        if not self.log_file_path.exists():
            # File doesn't exist yet - Fluent Bit might not have started writing
            return 0
        
        try:
            current_size = self.log_file_path.stat().st_size
            
            # Check if file was rotated or truncated
            if current_size < self.last_position:
                self.last_position = 0
            
            # Read new content
            new_logs = []
            if current_size > self.last_position:
                with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    
                    for line in new_lines:
                        if line.strip():
                            try:
                                # Try parsing as JSON first (standard JSON lines format)
                                entry = json.loads(line)
                                parsed = self._parse_fluent_bit_entry(entry)
                                new_logs.append(parsed)
                            except json.JSONDecodeError:
                                # Try parsing Fluent Bit default format
                                try:
                                    parsed = self._parse_fluent_bit_format(line)
                                    if parsed:
                                        new_logs.append(parsed)
                                except Exception as parse_error:
                                    logger.debug(f"Failed to parse line in refresh: {parse_error}")
                                    continue
                    
                    self.last_position = f.tell()
            
            # Add to cache
            self.log_cache.extend(new_logs)
            
            # Trim cache if too large
            if len(self.log_cache) > self.max_cache_size:
                excess = len(self.log_cache) - self.max_cache_size
                self.log_cache = self.log_cache[excess:]
            
            if new_logs:
                logger.debug(f"Refreshed {len(new_logs)} new Fluent Bit logs")
            
            return len(new_logs)
        except Exception as e:
            logger.error(f"Error reading Fluent Bit logs: {e}")
            return 0
    
    def get_recent_logs(self, limit: int = 100, service: Optional[str] = None, 
                       level: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            service: Filter by service name
            level: Filter by log level
            tag: Filter by Fluent Bit tag
        
        Returns:
            List of log entries
        """
        # Refresh logs first
        self.refresh_logs()
        
        # Filter logs
        filtered = self.log_cache.copy()
        
        if service:
            filtered = [log for log in filtered if log.get('service', '').lower() == service.lower()]
        
        if level:
            filtered = [log for log in filtered if log.get('level', '').upper() == level.upper()]
        
        if tag:
            filtered = [log for log in filtered if tag.lower() in log.get('tag', '').lower()]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return limited results
        return filtered[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about Fluent Bit logs"""
        self.refresh_logs()
        
        total_logs = len(self.log_cache)
        
        # Count by level
        by_level = {}
        by_service = {}
        by_tag = {}
        
        for log in self.log_cache:
            level = log.get('level', 'INFO')
            service = log.get('service', 'unknown')
            tag = log.get('tag', 'unknown')
            
            by_level[level] = by_level.get(level, 0) + 1
            by_service[service] = by_service.get(service, 0) + 1
            by_tag[tag] = by_tag.get(tag, 0) + 1
        
        return {
            'total_logs': total_logs,
            'by_level': by_level,
            'by_service': by_service,
            'by_tag': by_tag,
            'cache_size': len(self.log_cache)
        }
    
    def get_sources(self) -> List[str]:
        """Get list of available log sources/tags"""
        self.refresh_logs()
        tags = set()
        for log in self.log_cache:
            tag = log.get('tag', 'unknown')
            if tag:
                tags.add(tag)
        return sorted(list(tags))


# Global Fluent Bit reader instance
fluent_bit_reader = None


def initialize_fluent_bit_reader(log_file_path: str = '/var/log/fluent-bit/fluent-bit-output.jsonl'):
    """Initialize global Fluent Bit reader"""
    global fluent_bit_reader
    try:
        fluent_bit_reader = FluentBitReader(log_file_path)
        logger.info(f"Fluent Bit reader initialized (log file: {log_file_path})")
        return fluent_bit_reader
    except Exception as e:
        logger.error(f"Failed to initialize Fluent Bit reader: {e}")
        return None

