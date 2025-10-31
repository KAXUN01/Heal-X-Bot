"""
Centralized Log Aggregation System
Collects logs from all discovered services and programs into a single centralized log file
"""

import os
import time
import json
import logging
import threading
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
from service_discovery import ServiceDiscovery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CentralizedLogger:
    """
    Aggregates logs from multiple sources into a centralized log file
    """
    
    def __init__(self, output_dir: str = './logs/centralized'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Central log file
        self.central_log_file = self.output_dir / 'centralized.log'
        self.json_log_file = self.output_dir / 'centralized.json'
        
        # Service discovery
        self.discovery = ServiceDiscovery()
        self.log_sources = {}
        self.file_positions = {}
        
        # Aggregation thread
        self.running = False
        self.aggregation_thread = None
        
        # Statistics
        self.stats = {
            'total_logs_collected': 0,
            'logs_by_service': defaultdict(int),
            'start_time': None,
            'last_collection_time': None
        }
        
        # Index for quick search
        self.log_index = []
        
        # Track seen logs to prevent duplicates (using message hash + timestamp)
        # Format: {log_hash: timestamp_when_seen}
        self.seen_logs = {}
        self.duplicate_window_seconds = 5  # Ignore duplicates within 5 seconds
        self.initial_load_complete = False  # Track if initial bulk load is done
        
        # Track systemd journal cursor for incremental collection
        self.journal_cursor = None
        self.journal_cursor_file = self.output_dir / '.journal_cursor'
        
        # Load journal cursor if exists
        if self.journal_cursor_file.exists():
            try:
                with open(self.journal_cursor_file, 'r') as f:
                    self.journal_cursor = f.read().strip()
            except:
                pass
        
        # Log file size limits (50MB maximum)
        self.max_log_size_bytes = 50 * 1024 * 1024  # 50 MB
        self.check_rotation_counter = 0  # Check every N collections
        
        # Clean old user@ logs from index on startup (but only after log_index is populated)
        # We'll call this after index is loaded from files
    
    def _clean_user_logs_from_index(self):
        """
        Remove user@ service logs from the index
        """
        original_count = len(self.log_index)
        self.log_index = [
            log for log in self.log_index
            if not any([
                'systemd-user@' in log.get('service', '').lower(),
                'user@1000' in log.get('service', '').lower(),
                log.get('service', '').lower() == 'user',
                log.get('service', '').lower() == 'systemd-user',
                log.get('service', '').lower().startswith('user@'),
                'user@1000' in log.get('message', '').lower(),
                'systemd-user@' in log.get('message', '').lower(),
                'systemd-user@1000.service' in log.get('message', '').lower(),
                'systemd-user@1000' in log.get('source_file', '').lower(),
                'user@1000.service' in log.get('source_file', '').lower()
            ])
        ]
        removed = original_count - len(self.log_index)
        if removed > 0:
            logger.info(f"Cleaned {removed} user@ service logs from index")
    
    def discover_and_setup(self):
        """
        Discover all services and set up log collection
        """
        logger.info("Discovering services and log locations...")
        
        # Run service discovery
        self.discovery.discover_all_services()
        log_locations = self.discovery.get_log_locations()
        
        # Setup log sources and collect initial logs
        for service_name, log_files in log_locations.items():
            for log_info in log_files:
                log_path = log_info['path']
                self.log_sources[log_path] = {
                    'service': service_name,
                    'path': log_path,
                    'size': log_info['size'],
                    'last_modified': log_info['modified']
                }
                # Collect initial recent logs (last 500 lines) and then set position to end
                try:
                    path = Path(log_path)
                    if path.exists() and path.is_file():
                        # Read last 500 lines for initial collection
                        try:
                            file_size = path.stat().st_size
                            # For large files, use tail approach; for small files, read all
                            if file_size > 10 * 1024 * 1024:  # > 10MB, use tail command
                                result = subprocess.run(
                                    ['tail', '-n', '500', str(log_path)],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if result.returncode == 0:
                                    initial_lines = result.stdout.splitlines()
                                else:
                                    initial_lines = []
                            else:
                                # Small file, read directly
                                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = f.readlines()
                                    if len(lines) > 500:
                                        initial_lines = lines[-500:]
                                    else:
                                        initial_lines = lines
                            
                            # Process initial lines
                            initial_count = 0
                            for line in initial_lines:
                                if line.strip():
                                    self._write_to_central_log(line, {
                                        'service': service_name,
                                        'path': log_path
                                    })
                                    initial_count += 1
                            
                            # Now set position to end for future incremental collection
                            self.file_positions[log_path] = path.stat().st_size
                            if initial_count > 0:
                                logger.info(f"Collected {initial_count} initial logs from {log_path}")
                        except PermissionError:
                            logger.warning(f"No permission to read {log_path} - user may need to be in 'adm' group")
                            self.file_positions[log_path] = 0
                        except Exception as e:
                            logger.warning(f"Could not read initial logs from {log_path}: {e}")
                            self.file_positions[log_path] = 0
                    else:
                        self.file_positions[log_path] = 0
                except Exception as e:
                    logger.warning(f"Error setting up {log_path}: {e}")
                    self.file_positions[log_path] = 0
        
        logger.info(f"Setup complete. Monitoring {len(self.log_sources)} log files from {len(log_locations)} services")
        
        # Mark initial load as complete after a short delay (to allow bulk processing)
        import threading
        def mark_initial_load_done():
            time.sleep(10)  # Wait 10 seconds for initial processing
            self.initial_load_complete = True
            logger.info("Initial log load complete, now in incremental mode")
        
        threading.Thread(target=mark_initial_load_done, daemon=True).start()
        
        # Save discovery results
        self._save_source_mapping()
    
    def start_collection(self):
        """
        Start the log collection process
        """
        if self.running:
            logger.warning("Log collection already running")
            return
        
        # Clean old user@ logs before starting
        self._clean_user_logs_from_index()
        self.running = True
        self.stats['start_time'] = datetime.now().isoformat()
        
        # Start aggregation thread
        self.aggregation_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.aggregation_thread.start()
        
        logger.info("Centralized log collection started")
    
    def stop_collection(self):
        """
        Stop the log collection process
        """
        self.running = False
        if self.aggregation_thread:
            self.aggregation_thread.join(timeout=5)
        
        logger.info("Centralized log collection stopped")
    
    def _collection_loop(self):
        """
        Main collection loop - runs in background thread
        """
        while self.running:
            try:
                self._collect_logs()
                self.stats['last_collection_time'] = datetime.now().isoformat()
                
                # Check and maintain log file size every 10 collections (every ~20 seconds)
                self.check_rotation_counter += 1
                if self.check_rotation_counter >= 10:
                    self._maintain_log_file_size()
                    self.check_rotation_counter = 0
                
                time.sleep(2)  # Check for new logs every 2 seconds
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(5)
    
    def _collect_logs(self):
        """
        Collect new log entries from all sources
        """
        # Collect from systemd journal (system-wide logs)
        self._collect_from_journal()
        
        # Collect from discovered log files
        for log_path, source_info in self.log_sources.items():
            try:
                self._collect_from_source(log_path, source_info)
            except Exception as e:
                logger.error(f"Error collecting from {log_path}: {e}")
    
    def _collect_from_journal(self):
        """
        Collect logs from systemd journal (system-wide logs)
        Collects from both system and user journals, but filters out user@ session noise
        """
        try:
            # First, try to collect from system journal (all system services)
            # Use --system to get system-level logs explicitly
            cmd = ['journalctl', '--system', '--output=json', '--no-pager', '-n', '150']
            
            # Use cursor if available for incremental collection
            if self.journal_cursor:
                cmd.extend(['--after-cursor', self.journal_cursor])
            else:
                # First run: get last 500 entries to populate initial collection
                cmd = ['journalctl', '--system', '--output=json', '--no-pager', '-n', '500']
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Also collect from user journal but filter better
            # This is a fallback/secondary collection
            user_cmd = ['journalctl', '--user', '--output=json', '--no-pager', '-n', '50', '--since', '2 minutes ago']
            user_result = subprocess.run(
                user_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            collected_count = 0
            
            # Process system journal entries
            if result.returncode != 0:
                logger.warning(f"journalctl --system returned non-zero exit code: {result.returncode}")
                if result.stderr:
                    logger.warning(f"journalctl error: {result.stderr[:200]}")
            elif result.stdout.strip():
                system_entries = 0
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            parsed = self._parse_journal_entry(entry)
                            if parsed and parsed.get('message'):
                                # Filter out user@ services from system journal (they shouldn't be here but check anyway)
                                service_name = parsed.get('service', '').lower()
                                if 'user@' not in service_name:
                                    source_info = {
                                        'service': parsed.get('service', 'system'),
                                        'path': 'systemd-journal'
                                    }
                                    log_entry = {
                                        'timestamp': parsed.get('timestamp'),
                                        'service': parsed.get('service', 'system'),
                                        'source_file': 'systemd-journal',
                                        'message': parsed.get('message', ''),
                                        'level': parsed.get('level', 'INFO')
                                    }
                                    self._write_log_entry(log_entry, source_info)
                                    collected_count += 1
                                    system_entries += 1
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.debug(f"Failed to parse journal entry: {e}")
                            continue
                
                if system_entries == 0 and collected_count == 0:
                    logger.warning("No system journal entries collected - check journal permissions")
            
            # Process user journal entries (filter out user@ session noise)
            if user_result.returncode == 0 and user_result.stdout.strip():
                for line in user_result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            unit = entry.get('_SYSTEMD_UNIT', '')
                            
                            # Skip user@ session services - they're just noise
                            if 'user@' in unit:
                                continue
                            
                            parsed = self._parse_journal_entry(entry)
                            if parsed and parsed.get('message'):
                                source_info = {
                                    'service': parsed.get('service', 'system'),
                                    'path': 'systemd-journal-user'
                                }
                                log_entry = {
                                    'timestamp': parsed.get('timestamp'),
                                    'service': parsed.get('service', 'system'),
                                    'source_file': 'systemd-journal-user',
                                    'message': parsed.get('message', ''),
                                    'level': parsed.get('level', 'INFO')
                                }
                                self._write_log_entry(log_entry, source_info)
                                collected_count += 1
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            continue
            
            if collected_count > 0:
                logger.info(f"Collected {collected_count} new entries from journal (system-wide logs)")
                
                # Log sample of services collected for debugging
                sample_services = set()
                for entry in self.log_index[-collected_count:]:
                    if entry.get('source_file') == 'systemd-journal' or entry.get('source_file') == 'systemd-journal-user':
                        service = entry.get('service', 'unknown')
                        if 'user@' not in service.lower():
                            sample_services.add(service)
                if sample_services:
                    logger.info(f"Services collected from journal: {', '.join(sorted(list(sample_services)[:15]))}")
                else:
                    logger.warning("No services collected from journal - check filters")
            
            # Update cursor from system journal (most recent)
            cursor_result = subprocess.run(
                ['journalctl', '--system', '-n', '1', '--show-cursor', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if cursor_result.returncode == 0 and 'cursor:' in cursor_result.stdout:
                self.journal_cursor = cursor_result.stdout.split('cursor: ')[1].strip()
                # Save cursor
                try:
                    with open(self.journal_cursor_file, 'w') as f:
                        f.write(self.journal_cursor)
                except:
                    pass
        
        except subprocess.TimeoutExpired:
            logger.warning("journalctl timeout - system may be slow")
        except FileNotFoundError:
            logger.error("journalctl not available - cannot collect system logs")
        except Exception as e:
            logger.error(f"Error collecting from journal: {e}", exc_info=True)
    
    def _parse_journal_entry(self, entry: Dict) -> Dict[str, Any]:
        """
        Parse a systemd journal entry - extracts all system services
        """
        try:
            # Convert timestamp
            timestamp_us = int(entry.get('__REALTIME_TIMESTAMP', 0))
            if timestamp_us == 0:
                return None
            timestamp = datetime.fromtimestamp(timestamp_us / 1000000)
            
            # Get service name - prioritize _SYSTEMD_UNIT over SYSLOG_IDENTIFIER
            service = entry.get('_SYSTEMD_UNIT', '') or entry.get('_USER_UNIT', '') or entry.get('SYSLOG_IDENTIFIER', '')
            
            # Skip user@ session services immediately (these are just noise)
            if service and 'user@' in service.lower():
                return None
            
            # Clean up service name
            if not service:
                service = 'system'
            else:
                # Remove common suffixes
                if service.endswith('.service'):
                    service = service[:-8]
                if service.endswith('.scope'):
                    service = service[:-6]
                if service.endswith('.slice'):
                    service = service[:-6]
                # Handle other @ services - extract base name (e.g., ssh@192.168.1.1 -> ssh)
                if '@' in service:
                    # Extract base service name (e.g., ssh@192.168.1.1 -> ssh)
                    parts = service.split('@')
                    service = parts[0]
            
            # Get message
            message = entry.get('MESSAGE', '').strip()
            if not message:
                return None  # Skip entries without messages
            
            # Get priority/level
            priority = int(entry.get('PRIORITY', 6))
            if priority <= 2:
                level = 'CRITICAL'
            elif priority == 3:
                level = 'ERROR'
            elif priority == 4:
                level = 'WARNING'
            elif priority == 5:
                level = 'NOTICE'
            elif priority == 6:
                level = 'INFO'
            else:
                level = 'DEBUG'
            
            # Get additional context
            syslog_id = entry.get('SYSLOG_IDENTIFIER', '')
            comm = entry.get('_COMM', '')
            
            # Prefer more descriptive service name if available
            if syslog_id and syslog_id != service:
                # Use syslog identifier if it's more meaningful (not just the unit name)
                if len(syslog_id) > 2 and not syslog_id.startswith('systemd'):
                    service = syslog_id
            
            return {
                'timestamp': timestamp.isoformat(),
                'service': service,
                'message': message,
                'level': level,
                'priority': priority,
                'source': 'systemd-journal',
                'syslog_identifier': syslog_id,
                'command': comm
            }
        except (KeyError, ValueError, OSError) as e:
            logger.debug(f"Error parsing journal entry: {e}")
            return None
    
    def _collect_from_source(self, log_path: str, source_info: Dict[str, Any]):
        """
        Collect new logs from a single source file
        """
        try:
            path = Path(log_path)
            if not path.exists():
                return
            
            current_size = path.stat().st_size
            last_position = self.file_positions.get(log_path, 0)
            
            # Check if file was rotated or truncated
            if current_size < last_position:
                last_position = 0
            
            # Read new content
            if current_size > last_position:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    # Process each new line
                    for line in new_lines:
                        if line.strip():  # Skip empty lines
                            self._write_to_central_log(line, source_info)
                    
                    # Update position
                    self.file_positions[log_path] = f.tell()
        
        except Exception as e:
            logger.error(f"Error reading {log_path}: {e}")
    
    def _write_log_entry(self, log_entry: Dict[str, Any], source_info: Dict[str, Any]):
        """
        Write a parsed log entry directly (used for journal entries)
        """
        # Filter out systemd-user@1000.service logs completely
        service_name = log_entry.get('service', '').lower()
        if 'systemd-user@' in service_name or 'user@1000' in service_name or service_name == 'user':
            return  # Skip these logs entirely
        
        # Also check message content
        message_clean = log_entry.get('message', '').strip()
        if 'user@1000' in message_clean.lower() or 'systemd-user@' in message_clean.lower():
            return  # Skip logs about user@ services
        
        # Check for duplicates
        try:
            source_path = source_info.get('path', 'unknown')
            log_hash = hashlib.md5(f"{message_clean}|{log_entry.get('service', '')}|{source_path}|{log_entry.get('timestamp', '')}".encode()).hexdigest()
        except:
            log_hash = hashlib.md5(f"{message_clean}|{log_entry.get('service', '')}".encode()).hexdigest()
        
        # Check if we've seen this log recently (skip check during initial bulk load)
        current_time = time.time()
        if log_hash in self.seen_logs and self.initial_load_complete:
            last_seen = self.seen_logs[log_hash]
            if current_time - last_seen < self.duplicate_window_seconds:
                return  # Skip duplicate
        
        # Record when we saw this log
        self.seen_logs[log_hash] = current_time
        
        # Clean old entries periodically
        if len(self.seen_logs) > 5000:
            cutoff_time = current_time - 60
            self.seen_logs = {k: v for k, v in self.seen_logs.items() if v > cutoff_time}
        
        timestamp = log_entry.get('timestamp', datetime.now().isoformat())
        service_name = log_entry.get('service', source_info.get('service', 'unknown'))
        source_path = source_info.get('path', 'unknown')
        message = log_entry.get('message', '')
        level = log_entry.get('level', self._detect_log_level(message))
        
        # Write to text log file
        with open(self.central_log_file, 'a', encoding='utf-8') as f:
            formatted_log = f"[{timestamp}] [{service_name}] {message}"
            f.write(formatted_log)
            if not formatted_log.endswith('\n'):
                f.write('\n')
        
        # Write to JSON log file
        final_entry = {
            'timestamp': timestamp,
            'service': service_name,
            'source_file': source_path,
            'message': message,
            'level': level
        }
        with open(self.json_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(final_entry) + '\n')
        
        # Update statistics
        self.stats['total_logs_collected'] += 1
        self.stats['logs_by_service'][service_name] += 1
        
        # Add to index (but skip user@ services)
        service_check = final_entry.get('service', '').lower()
        message_check = final_entry.get('message', '').lower()
        if ('systemd-user@' not in service_check and 'user@1000' not in service_check and 
            service_check != 'user' and 'user@1000' not in message_check and 
            'systemd-user@' not in message_check):
            self.log_index.append(final_entry)
            if len(self.log_index) > 10000:
                self.log_index.pop(0)
    
    def _write_to_central_log(self, log_line: str, source_info: Dict[str, Any]):
        """
        Write a log entry to the centralized log file
        """
        # Filter out systemd-user@1000.service logs completely - they're just noise
        service_name = source_info.get('service', '').lower()
        if 'systemd-user@' in service_name or 'user@1000' in service_name:
            return  # Skip these logs entirely
        
        # Also check if the log message itself contains user@ references
        message_clean = log_line.strip()
        if 'user@1000' in message_clean.lower() or 'systemd-user@' in message_clean.lower():
            return  # Skip logs about user@ services
        
        # Use source file modification time + message content to create unique hash
        # This prevents duplicates when the same log line appears multiple times
        # Create a hash of message + service + source path
        # This allows same message from different services/times to be unique
        try:
            source_path = source_info['path']
            log_hash = hashlib.md5(f"{message_clean}|{source_info['service']}|{source_path}".encode()).hexdigest()
        except:
            # Fallback: use message + service
            log_hash = hashlib.md5(f"{message_clean}|{source_info['service']}".encode()).hexdigest()
        
        # Check if we've seen this log recently (within duplicate window)
        # Skip duplicate check during initial bulk load to allow all logs through
        current_time = time.time()
        if log_hash in self.seen_logs and self.initial_load_complete:
            last_seen = self.seen_logs[log_hash]
            # If seen within the window, skip it
            if current_time - last_seen < self.duplicate_window_seconds:
                return  # Skip duplicate
        
        # Record when we saw this log
        self.seen_logs[log_hash] = current_time
        
        # Clean old entries periodically (remove entries older than 1 minute)
        if len(self.seen_logs) > 5000:
            cutoff_time = current_time - 60  # 1 minute ago
            self.seen_logs = {k: v for k, v in self.seen_logs.items() if v > cutoff_time}
        
        # Try to parse timestamp and service from log line (for syslog/kern/auth.log format)
        timestamp = datetime.now().isoformat()
        extracted_service = service_name
        extracted_message = message_clean
        
        # Parse syslog-style format: "2025-10-30T09:09:06.975540+05:30 hostname service: message"
        # Or: "Oct 30 09:09:06 hostname service: message"
        try:
            # Try ISO format first
            if 'T' in message_clean and len(message_clean) > 20:
                parts = message_clean.split(' ', 3)
                if len(parts) >= 4:
                    try:
                        # ISO timestamp: 2025-10-30T09:09:06.975540+05:30
                        iso_timestamp = parts[0] + ' ' + parts[1]
                        parsed_time = datetime.fromisoformat(iso_timestamp)
                        timestamp = parsed_time.isoformat()
                        
                        # Extract service from the log line
                        # Format: hostname service: message
                        remaining = parts[3] if len(parts) > 3 else parts[2]
                        if ':' in remaining:
                            service_part = remaining.split(':', 1)[0].strip()
                            # Remove hostname if present
                            service_part = service_part.split()[-1] if ' ' in service_part else service_part
                            if service_part:
                                extracted_service = service_part
                            extracted_message = remaining.split(':', 1)[1].strip() if ':' in remaining else remaining
                    except (ValueError, IndexError):
                        # Fallback: try standard syslog format
                        pass
            
            # Try standard syslog format: "Oct 30 09:09:06 hostname service: message"
            if timestamp == datetime.now().isoformat() and len(message_clean) > 15:
                # Check if it starts with a month name
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                first_word = message_clean.split()[0] if message_clean.split() else ''
                if first_word in months:
                    parts = message_clean.split(':', 2)
                    if len(parts) >= 3:
                        # Extract service name
                        service_part = parts[1].strip() if len(parts) > 1 else ''
                        if service_part:
                            # Remove hostname
                            service_words = service_part.split()
                            if len(service_words) > 1:
                                extracted_service = service_words[-1]
                            else:
                                extracted_service = service_part
                        extracted_message = parts[2].strip() if len(parts) > 2 else message_clean
        except Exception:
            pass  # Use defaults if parsing fails
        
        service_name = extracted_service if extracted_service else source_info['service']
        source_path = source_info['path']
        
        # Create structured log entry
        log_entry = {
            'timestamp': timestamp,
            'service': service_name,
            'source_file': source_path,
            'message': extracted_message if extracted_message else message_clean,
            'level': self._detect_log_level(extracted_message if extracted_message else message_clean)  # Auto-detect log level
        }
        
        # Write to text log file (human-readable)
        with open(self.central_log_file, 'a', encoding='utf-8') as f:
            formatted_log = f"[{timestamp}] [{service_name}] {message_clean}"
            f.write(formatted_log)
            if not formatted_log.endswith('\n'):
                f.write('\n')
        
        # Write to JSON log file (machine-readable)
        with open(self.json_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Update statistics
        self.stats['total_logs_collected'] += 1
        self.stats['logs_by_service'][service_name] += 1
        
        # Add to index (but skip user@ services, keep last 10000 entries)
        service_check = log_entry.get('service', '').lower()
        message_check = log_entry.get('message', '').lower()
        if ('systemd-user@' not in service_check and 'user@1000' not in service_check and 
            service_check != 'user' and 'user@1000' not in message_check and 
            'systemd-user@' not in message_check):
            self.log_index.append(log_entry)
            if len(self.log_index) > 10000:
                self.log_index.pop(0)
    
    def _detect_log_level(self, message: str) -> str:
        """
        Auto-detect log level from message content
        """
        msg_lower = message.lower()
        if any(keyword in msg_lower for keyword in ['critical', 'fatal', 'emergency', 'panic']):
            return 'CRITICAL'
        elif any(keyword in msg_lower for keyword in ['error', 'err', 'failed', 'failure']):
            return 'ERROR'
        elif any(keyword in msg_lower for keyword in ['warn', 'warning', 'caution']):
            return 'WARNING'
        elif any(keyword in msg_lower for keyword in ['debug', 'dbg']):
            return 'DEBUG'
        else:
            return 'INFO'
    
    def _save_source_mapping(self):
        """
        Save the mapping of services to log file locations
        """
        mapping_file = self.output_dir / 'log_source_mapping.json'
        
        mapping = {
            'timestamp': datetime.now().isoformat(),
            'total_services': len(set(info['service'] for info in self.log_sources.values())),
            'total_log_files': len(self.log_sources),
            'sources': self.log_sources,
            'discovery_summary': self.discovery.get_summary()
        }
        
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
        
        logger.info(f"Source mapping saved to {mapping_file}")
    
    def search_logs(self, query: str, service: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search through centralized logs
        """
        results = []
        
        for entry in reversed(self.log_index):
            # Filter out user@ service logs
            entry_service = entry.get('service', '').lower()
            if ('systemd-user@' in entry_service or 
                'user@1000' in entry_service or 
                entry_service == 'user' or 
                entry_service == 'systemd-user' or
                entry_service.startswith('user@')):
                continue
            
            # Apply filters
            if service and entry['service'] != service:
                continue
            
            if query.lower() in entry['message'].lower():
                results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_logs_by_service(self, service: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get logs for a specific service
        """
        # Don't allow querying user@ services
        service_lower = service.lower()
        if ('systemd-user@' in service_lower or 
            'user@1000' in service_lower or 
            service_lower == 'user' or 
            service_lower == 'systemd-user' or
            service_lower.startswith('user@')):
            return []
        
        results = []
        
        for entry in reversed(self.log_index):
            # Also filter out user@ services even if not explicitly requested
            entry_service = entry.get('service', '').lower()
            if ('systemd-user@' in entry_service or 
                'user@1000' in entry_service or 
                entry_service == 'user' or 
                entry_service == 'systemd-user' or
                entry_service.startswith('user@')):
                continue
            
            if entry['service'] == service:
                results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent logs, prioritizing journal entries and filtering out user@ services
        """
        # Filter out user@ service logs completely
        filtered_logs = []
        for log in self.log_index:
            service = log.get('service', '').lower()
            message = log.get('message', '').lower()
            source_file = log.get('source_file', '').lower()
            # Skip user@ logs - check multiple variations
            if ('systemd-user@' in service or 
                'user@1000' in service or 
                service == 'user' or 
                service == 'systemd-user' or
                service.startswith('user@') or
                'systemd-user@1000' in source_file or
                'user@1000.service' in source_file):
                continue
            if 'user@1000' in message or 'systemd-user@' in message or 'systemd-user@1000.service' in message:
                continue
            filtered_logs.append(log)
        
        # Get all logs and sort by timestamp (newest first)
        all_logs = sorted(filtered_logs, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Prioritize journal entries - put them at the top
        journal_logs = [log for log in all_logs if log.get('source_file', '').startswith('systemd-journal')]
        other_logs = [log for log in all_logs if not log.get('source_file', '').startswith('systemd-journal')]
        
        # Combine: journal logs first, then others, then limit
        combined = journal_logs[:limit] + other_logs[:limit]
        return combined[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get collection statistics
        """
        return {
            **self.stats,
            'logs_by_service': dict(self.stats['logs_by_service']),
            'total_sources': len(self.log_sources),
            'total_services': len(set(info['service'] for info in self.log_sources.values())),
            'collection_status': 'running' if self.running else 'stopped',
            'central_log_file': str(self.central_log_file),
            'json_log_file': str(self.json_log_file),
            'index_size': len(self.log_index)
        }
    
    def get_service_list(self) -> List[str]:
        """
        Get list of all services being monitored
        """
        return sorted(set(info['service'] for info in self.log_sources.values()))
    
    def _maintain_log_file_size(self):
        """
        Maintain log file size by truncating when it exceeds 50MB
        Keeps the most recent logs (last 25MB) and removes older logs
        """
        for log_file in [self.central_log_file, self.json_log_file]:
            try:
                if not log_file.exists():
                    continue
                
                current_size = log_file.stat().st_size
                
                # If file exceeds 50MB, truncate to keep last 25MB
                if current_size > self.max_log_size_bytes:
                    keep_size = self.max_log_size_bytes // 2  # Keep last 25MB (half of max)
                    logger.info(f"Log file {log_file.name} exceeded 50MB ({current_size / (1024*1024):.2f}MB), truncating to keep last 25MB...")
                    
                    # Read the last portion of the file
                    with open(log_file, 'rb') as f:
                        f.seek(-keep_size, os.SEEK_END)
                        # Skip to next line to avoid partial line
                        f.readline()
                        remaining_content = f.read()
                    
                    # Write truncated content back
                    with open(log_file, 'wb') as f:
                        # Add a marker line indicating truncation
                        truncate_msg = f"\n[{datetime.now().isoformat()}] [SYSTEM] Log file truncated from {current_size / (1024*1024):.2f}MB to keep last {keep_size / (1024*1024):.2f}MB\n"
                        f.write(truncate_msg.encode())
                        f.write(remaining_content)
                    
                    new_size = log_file.stat().st_size
                    logger.info(f"Log file truncated: {new_size / (1024*1024):.2f}MB")
                    
                    # Also clean up log_index to match (keep last 5000 entries)
                    if len(self.log_index) > 5000:
                        excess = len(self.log_index) - 5000
                        self.log_index = self.log_index[excess:]
                        logger.debug(f"Cleaned up log index, removed {excess} old entries")
                        
            except Exception as e:
                logger.error(f"Error maintaining log file size for {log_file}: {e}")
    
    def rotate_logs(self, max_size_mb: int = 50):
        """
        Rotate log files if they exceed max size (legacy method, now using _maintain_log_file_size)
        """
        self.max_log_size_bytes = max_size_mb * 1024 * 1024
        self._maintain_log_file_size()
    
    def export_logs(self, output_file: str, format: str = 'json', 
                   service: str = None, query: str = None):
        """
        Export logs to a file
        """
        if query:
            logs = self.search_logs(query, service=service, limit=10000)
        elif service:
            logs = self.get_logs_by_service(service, limit=10000)
        else:
            logs = self.get_recent_logs(limit=10000)
        
        with open(output_file, 'w') as f:
            if format == 'json':
                json.dump(logs, f, indent=2)
            else:  # text format
                for log in logs:
                    f.write(f"[{log['timestamp']}] [{log['service']}] {log['message']}\n")
        
        logger.info(f"Exported {len(logs)} logs to {output_file}")


# Global centralized logger instance
centralized_logger = None


def initialize_centralized_logging(output_dir: str = './logs/centralized'):
    """
    Initialize the centralized logging system
    """
    global centralized_logger
    
    centralized_logger = CentralizedLogger(output_dir=output_dir)
    
    # Discover services and setup
    centralized_logger.discover_and_setup()
    
    # Start collection
    centralized_logger.start_collection()
    
    logger.info("Centralized logging system initialized")
    return centralized_logger


if __name__ == "__main__":
    # Test the centralized logger
    print("="*60)
    print("CENTRALIZED LOG AGGREGATION SYSTEM")
    print("="*60)
    
    # Initialize
    clogger = initialize_centralized_logging()
    
    try:
        # Run for a while to collect logs
        print("\nCollecting logs... (Press Ctrl+C to stop)")
        while True:
            time.sleep(10)
            
            # Print statistics
            stats = clogger.get_statistics()
            print(f"\n{'='*60}")
            print(f"Total Logs Collected: {stats['total_logs_collected']}")
            print(f"Services Monitored: {stats['total_services']}")
            print(f"Log Sources: {stats['total_sources']}")
            print(f"Status: {stats['collection_status']}")
            print(f"Central Log: {stats['central_log_file']}")
            print(f"{'='*60}")
            
            # Show top services
            if stats['logs_by_service']:
                print("\nTop Services by Log Count:")
                sorted_services = sorted(stats['logs_by_service'].items(), 
                                       key=lambda x: x[1], reverse=True)
                for service, count in sorted_services[:5]:
                    print(f"  {service}: {count} logs")
    
    except KeyboardInterrupt:
        print("\n\nStopping centralized logging...")
        clogger.stop_collection()
        
        # Final statistics
        final_stats = clogger.get_statistics()
        print(f"\n{'='*60}")
        print("FINAL STATISTICS")
        print(f"{'='*60}")
        print(f"Total Logs Collected: {final_stats['total_logs_collected']}")
        print(f"Services Monitored: {final_stats['total_services']}")
        print(f"Central Log File: {final_stats['central_log_file']}")
        print(f"JSON Log File: {final_stats['json_log_file']}")
        print(f"{'='*60}")

