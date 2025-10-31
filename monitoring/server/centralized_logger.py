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
from pathlib import Path
from datetime import datetime
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
        self.seen_logs = set()
        
    def discover_and_setup(self):
        """
        Discover all services and set up log collection
        """
        logger.info("Discovering services and log locations...")
        
        # Run service discovery
        self.discovery.discover_all_services()
        log_locations = self.discovery.get_log_locations()
        
        # Setup log sources
        for service_name, log_files in log_locations.items():
            for log_info in log_files:
                log_path = log_info['path']
                self.log_sources[log_path] = {
                    'service': service_name,
                    'path': log_path,
                    'size': log_info['size'],
                    'last_modified': log_info['modified']
                }
                # Initialize file position to end of file (only collect new logs)
                try:
                    self.file_positions[log_path] = Path(log_path).stat().st_size
                except:
                    self.file_positions[log_path] = 0
        
        logger.info(f"Setup complete. Monitoring {len(self.log_sources)} log files from {len(log_locations)} services")
        
        # Save discovery results
        self._save_source_mapping()
    
    def start_collection(self):
        """
        Start the log collection process
        """
        if self.running:
            logger.warning("Log collection already running")
            return
        
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
                time.sleep(2)  # Check for new logs every 2 seconds
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(5)
    
    def _collect_logs(self):
        """
        Collect new log entries from all sources
        """
        for log_path, source_info in self.log_sources.items():
            try:
                self._collect_from_source(log_path, source_info)
            except Exception as e:
                logger.error(f"Error collecting from {log_path}: {e}")
    
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
    
    def _write_to_central_log(self, log_line: str, source_info: Dict[str, Any]):
        """
        Write a log entry to the centralized log file
        """
        # Use source file modification time + message content to create unique hash
        # This prevents duplicates when the same log line appears multiple times
        message_clean = log_line.strip()
        
        # Create a hash of message + service + source path (without timestamp to catch duplicates)
        # Use file modification time if available to differentiate same message at different times
        try:
            source_path = source_info['path']
            source_mtime = Path(source_path).stat().st_mtime if Path(source_path).exists() else 0
            log_hash = hashlib.md5(f"{message_clean}|{source_info['service']}|{source_path}|{source_mtime}".encode()).hexdigest()
        except:
            # Fallback: use message + service
            log_hash = hashlib.md5(f"{message_clean}|{source_info['service']}".encode()).hexdigest()
        
        # Skip if we've seen this exact log recently (within last 5 seconds)
        # This prevents rapid-fire duplicates from the same source
        if log_hash in self.seen_logs:
            return  # Skip duplicate
        
        # Add to seen set (will be cleaned periodically)
        self.seen_logs.add(log_hash)
        
        # Clean old hashes periodically (keep last 5000 to prevent memory bloat)
        if len(self.seen_logs) > 5000:
            # Remove oldest 1000 entries (simple cleanup)
            self.seen_logs = set(list(self.seen_logs)[-4000:])
        
        timestamp = datetime.now().isoformat()
        service_name = source_info['service']
        source_path = source_info['path']
        
        # Create structured log entry
        log_entry = {
            'timestamp': timestamp,
            'service': service_name,
            'source_file': source_path,
            'message': message_clean,
            'level': self._detect_log_level(message_clean)  # Auto-detect log level
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
        
        # Add to index (keep last 10000 entries)
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
        results = []
        
        for entry in reversed(self.log_index):
            if entry['service'] == service:
                results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get most recent logs
        """
        return list(reversed(self.log_index[-limit:]))
    
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
    
    def rotate_logs(self, max_size_mb: int = 100):
        """
        Rotate log files if they exceed max size
        """
        for log_file in [self.central_log_file, self.json_log_file]:
            try:
                if log_file.exists():
                    size_mb = log_file.stat().st_size / (1024 * 1024)
                    
                    if size_mb > max_size_mb:
                        # Rotate the file
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        rotated_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
                        rotated_path = log_file.parent / rotated_name
                        
                        log_file.rename(rotated_path)
                        logger.info(f"Rotated {log_file} to {rotated_path}")
            except Exception as e:
                logger.error(f"Error rotating {log_file}: {e}")
    
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

