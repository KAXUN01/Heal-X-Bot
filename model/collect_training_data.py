#!/usr/bin/env python3
"""
Data Collection Script for Predictive Maintenance Training

Collects system metrics and logs for training the predictive maintenance model.
Run this script periodically to build a dataset for model training.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemMetricsCollector:
    """Collect system metrics for training data"""
    
    def __init__(self, output_path: str = None):
        self.output_path = Path(output_path) if output_path else Path(__file__).parent / "training_data"
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.data_file = self.output_path / f"system_metrics_{datetime.now().strftime('%Y%m%d')}.csv"
        self.records = []
        
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network
            net_io = psutil.net_io_counters()
            connections = len(psutil.net_connections())
            
            # System load
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            record = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'network_in_bytes': net_io.bytes_recv,
                'network_out_bytes': net_io.bytes_sent,
                'connections_count': connections,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'load_avg_1min': load_avg[0],
                'load_avg_5min': load_avg[1],
                'load_avg_15min': load_avg[2],
                # Log patterns (would be collected from logs)
                'error_count': 0,  # TODO: Count from system logs
                'warning_count': 0,
                'critical_count': 0,
                'service_failures': 0,
                'auth_failures': 0,
                'ssh_attempts': 0
            }
            
            return record
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def collect_from_logs(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich record with log pattern data"""
        try:
            # Check system logs for errors
            log_paths = [
                '/var/log/syslog',
                '/var/log/auth.log',
                '/var/log/kern.log'
            ]
            
            error_count = 0
            warning_count = 0
            critical_count = 0
            
            # Count errors in last hour
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for log_path in log_paths:
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r') as f:
                            for line in f:
                                if 'ERROR' in line or 'CRITICAL' in line:
                                    error_count += 1
                                elif 'WARNING' in line:
                                    warning_count += 1
                    except Exception:
                        pass
            
            record['error_count'] = error_count
            record['warning_count'] = warning_count
            record['critical_count'] = critical_count
            
            # Check service status
            try:
                import subprocess
                result = subprocess.run(
                    ['systemctl', 'is-active', '--quiet'],
                    capture_output=True,
                    timeout=5
                )
                # Count failed services
                failed_services = subprocess.run(
                    ['systemctl', 'list-units', '--state=failed', '--no-legend'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                record['service_failures'] = len(failed_services.stdout.strip().split('\n')) if failed_services.stdout.strip() else 0
            except Exception:
                record['service_failures'] = 0
            
            return record
        except Exception as e:
            logger.warning(f"Error collecting log data: {e}")
            return record
    
    def save_record(self, record: Dict[str, Any]):
        """Save record to CSV"""
        try:
            # Load existing data
            if self.data_file.exists():
                df = pd.read_csv(self.data_file)
            else:
                df = pd.DataFrame()
            
            # Append new record
            new_df = pd.DataFrame([record])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Save
            df.to_csv(self.data_file, index=False)
            logger.info(f"Saved record to {self.data_file} (total: {len(df)} records)")
        except Exception as e:
            logger.error(f"Error saving record: {e}")
    
    def collect_continuously(self, interval_seconds: int = 60, duration_hours: float = None):
        """Collect metrics continuously"""
        logger.info(f"Starting continuous collection (interval: {interval_seconds}s)")
        if duration_hours:
            logger.info(f"Will collect for {duration_hours} hours")
        
        start_time = datetime.now()
        count = 0
        
        try:
            while True:
                # Collect metrics
                record = self.collect_metrics()
                if record:
                    # Enrich with log data
                    record = self.collect_from_logs(record)
                    # Save
                    self.save_record(record)
                    count += 1
                
                # Check duration
                if duration_hours:
                    elapsed = (datetime.now() - start_time).total_seconds() / 3600
                    if elapsed >= duration_hours:
                        logger.info(f"Collection complete. Collected {count} records over {elapsed:.2f} hours")
                        break
                
                # Wait for next interval
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info(f"Collection stopped by user. Collected {count} records")
        except Exception as e:
            logger.error(f"Error during collection: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect system metrics for training data')
    parser.add_argument('--output', type=str, default=None, help='Output directory for CSV files')
    parser.add_argument('--interval', type=int, default=60, help='Collection interval in seconds (default: 60)')
    parser.add_argument('--duration', type=float, default=None, help='Collection duration in hours (default: continuous)')
    parser.add_argument('--once', action='store_true', help='Collect once and exit')
    
    args = parser.parse_args()
    
    collector = SystemMetricsCollector(output_path=args.output)
    
    if args.once:
        logger.info("Collecting single sample...")
        record = collector.collect_metrics()
        if record:
            record = collector.collect_from_logs(record)
            collector.save_record(record)
            logger.info("Collection complete")
    else:
        collector.collect_continuously(
            interval_seconds=args.interval,
            duration_hours=args.duration
        )

if __name__ == '__main__':
    main()

