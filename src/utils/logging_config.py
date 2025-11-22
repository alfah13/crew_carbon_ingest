# src/utils/logging_config.py
"""
Logging configuration for the application
Provides colored console output only
"""
import logging
import sys
import os
from typing import Optional


# ANSI color codes for terminal output
class LogColors:
    """ANSI color codes for pretty terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Levels
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Green
    WARNING = '\033[33m'    # Yellow
    ERROR = '\033[31m'      # Red
    CRITICAL = '\033[35m'   # Magenta
    
    # Components
    TIME = '\033[90m'       # Gray
    NAME = '\033[34m'       # Blue


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log output"""
    
    FORMATS = {
        logging.DEBUG: f"{LogColors.TIME}%(asctime)s{LogColors.RESET} | {LogColors.DEBUG}DEBUG{LogColors.RESET}    | {LogColors.NAME}%(name)s{LogColors.RESET} | %(message)s",
        logging.INFO: f"{LogColors.TIME}%(asctime)s{LogColors.RESET} | {LogColors.INFO}INFO{LogColors.RESET}     | {LogColors.NAME}%(name)s{LogColors.RESET} | %(message)s",
        logging.WARNING: f"{LogColors.TIME}%(asctime)s{LogColors.RESET} | {LogColors.WARNING}WARNING{LogColors.RESET}  | {LogColors.NAME}%(name)s{LogColors.RESET} | %(message)s",
        logging.ERROR: f"{LogColors.TIME}%(asctime)s{LogColors.RESET} | {LogColors.ERROR}ERROR{LogColors.RESET}    | {LogColors.NAME}%(name)s{LogColors.RESET} | %(message)s",
        logging.CRITICAL: f"{LogColors.TIME}%(asctime)s{LogColors.RESET} | {LogColors.CRITICAL}CRITICAL{LogColors.RESET} | {LogColors.NAME}%(name)s{LogColors.RESET} | %(message)s",
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(
            log_fmt,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return formatter.format(record)


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure a logger with colored console output
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
               If None, reads from LOG_LEVEL environment variable or defaults to 'INFO'
    
    Returns:
        logging.Logger: Configured logger instance
    
    Example:
        logger = setup_logger(__name__)
        logger.info("Application started")
        logger.error("Something went wrong", exc_info=True)
    """
    # Get log level from parameter, environment, or default to INFO
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def configure_root_logger(level: str = 'INFO'):
    """
    Configure the root logger for the entire application
    Call this once at application startup
    
    Args:
        level: Logging level for root logger
    """
    level = os.getenv('LOG_LEVEL', level).upper()
    numeric_level = getattr(logging, level, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
