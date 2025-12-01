"""
Structured logging module for Weather Harvester.

Provides both human-readable console output and structured JSON logs.
"""

import logging
import json
import sys
from typing import Optional
from datetime import datetime
from .utils import get_log_dir, ensure_dir
import os


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    
    Each log record is formatted as a JSON object with timestamp,
    level, logger name, function, and message.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """
    Formatter for human-readable console output with colors (ANSI codes).
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize formatter.
        
        Args:
            use_colors: Whether to use ANSI color codes
        """
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors and sys.stderr.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with optional colors.
        
        Args:
            record: Log record to format
        
        Returns:
            Formatted log string
        """
        if self.use_colors:
            levelname = record.levelname
            color = self.COLORS.get(levelname, '')
            record.levelname = f"{color}{levelname}{self.RESET}"
        
        result = super().format(record)
        
        # Reset levelname for other handlers
        if self.use_colors:
            record.levelname = levelname
        
        return result


def setup_logger(
    name: str = 'weather_harvester',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_logs: bool = True,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger with both console and file handlers.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: auto-generated in log dir)
        json_logs: Whether to use JSON format for file logs
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Console handler (human-readable)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(HumanReadableFormatter(use_colors=True))
        logger.addHandler(console_handler)
    
    # File handler (JSON or human-readable)
    if log_file is None:
        log_dir = get_log_dir()
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'weather_harvester_{timestamp}.log')
    
    ensure_dir(os.path.dirname(log_file))
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    if json_logs:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(HumanReadableFormatter(use_colors=False))
    
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = 'weather_harvester') -> logging.Logger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Set up with defaults if not already configured
        return setup_logger(name)
    return logger


__all__ = [
    'JSONFormatter',
    'HumanReadableFormatter',
    'setup_logger',
    'get_logger',
]
