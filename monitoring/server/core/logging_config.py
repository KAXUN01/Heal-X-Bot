"""
Standardized logging configuration for all Heal-X-Bot services
Provides consistent logging setup across all services
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def get_log_level() -> int:
    """Get log level from environment variable"""
    level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return level_map.get(level_str, logging.INFO)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[int] = None,
    log_dir: str = "logs",
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup a standardized logger for a service
    
    Args:
        name: Logger name (typically __name__)
        log_file: Path to log file (relative to log_dir). If None, uses {name}.log
        level: Logging level. If None, uses LOG_LEVEL environment variable
        log_dir: Directory for log files
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    if level is None:
        level = get_log_level()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create log directory if needed
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Determine log file path
    if log_file is None:
        log_file = f"{name.split('.')[-1]}.log"
    log_file_path = log_path / log_file
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        str(log_file_path),
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    
    # Standard format for all logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler()
        # Console shows WARNING and above by default, or DEBUG if LOG_LEVEL is DEBUG
        console_level = logging.DEBUG if level == logging.DEBUG else logging.WARNING
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_service_logger(service_name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Get a pre-configured logger for a service
    
    Args:
        service_name: Name of the service (e.g., 'dashboard', 'model', 'monitoring-server')
        log_dir: Log directory path
    
    Returns:
        Configured logger
    """
    return setup_logger(
        name=service_name,
        log_file=f"{service_name}.log",
        log_dir=log_dir
    )

