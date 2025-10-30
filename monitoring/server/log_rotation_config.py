"""
Log Rotation Configuration
Automatic log file rotation and cleanup to prevent disk space issues
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

# Log Configuration
LOG_CONFIG = {
    'max_bytes': 5 * 1024 * 1024,  # 5 MB per log file
    'backup_count': 3,              # Keep 3 backup files (total: 20 MB per service)
    'log_level': logging.INFO,      # Default log level
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def setup_rotating_logger(name: str, log_file: str, level=logging.INFO):
    """
    Setup a logger with automatic rotation
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_CONFIG['max_bytes'],
        backupCount=LOG_CONFIG['backup_count']
    )
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        LOG_CONFIG['format'],
        datefmt=LOG_CONFIG['date_format']
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    # Also add console handler for immediate visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def cleanup_old_logs(log_directory: str, max_age_days: int = 7):
    """
    Delete log files older than specified days
    
    Args:
        log_directory: Directory containing log files
        max_age_days: Maximum age in days
    """
    import time
    
    try:
        log_path = Path(log_directory)
        if not log_path.exists():
            return
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        deleted_count = 0
        deleted_size = 0
        
        for log_file in log_path.glob('*.log*'):
            if log_file.is_file():
                file_age = current_time - log_file.stat().st_mtime
                
                if file_age > max_age_seconds:
                    file_size = log_file.stat().st_size
                    log_file.unlink()
                    deleted_count += 1
                    deleted_size += file_size
        
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} old log files, freed {deleted_size / 1024 / 1024:.2f} MB")
    
    except Exception as e:
        logging.error(f"Error cleaning up old logs: {e}")


def get_log_directory_size(log_directory: str) -> dict:
    """
    Get total size of log directory
    
    Args:
        log_directory: Directory to check
    
    Returns:
        Dictionary with size information
    """
    try:
        log_path = Path(log_directory)
        if not log_path.exists():
            return {'total_size': 0, 'file_count': 0}
        
        total_size = 0
        file_count = 0
        
        for log_file in log_path.glob('**/*.log*'):
            if log_file.is_file():
                total_size += log_file.stat().st_size
                file_count += 1
        
        return {
            'total_size': total_size,
            'total_size_mb': total_size / 1024 / 1024,
            'file_count': file_count
        }
    
    except Exception as e:
        logging.error(f"Error getting log directory size: {e}")
        return {'total_size': 0, 'file_count': 0}


# Predefined loggers for common services
def get_service_logger(service_name: str, log_dir: str = "logs"):
    """
    Get a pre-configured logger for a service
    
    Args:
        service_name: Name of the service (e.g., 'dashboard', 'model')
        log_dir: Log directory path
    
    Returns:
        Configured logger
    """
    log_file = os.path.join(log_dir, f"{service_name}.log")
    return setup_rotating_logger(service_name, log_file)


if __name__ == "__main__":
    # Test the logger
    test_logger = setup_rotating_logger('test', 'logs/test.log')
    test_logger.info("This is a test log entry")
    test_logger.warning("This is a warning")
    test_logger.error("This is an error")
    
    print("✅ Log rotation configured successfully")
    print(f"📊 Max file size: {LOG_CONFIG['max_bytes'] / 1024 / 1024} MB")
    print(f"📦 Backup count: {LOG_CONFIG['backup_count']}")
    print(f"💾 Total space per service: {(LOG_CONFIG['max_bytes'] * (LOG_CONFIG['backup_count'] + 1)) / 1024 / 1024} MB")

