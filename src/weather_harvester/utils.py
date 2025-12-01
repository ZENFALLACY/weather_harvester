"""
Utility functions and constants for Weather Harvester.

Provides shared helpers for file I/O, exit codes, and common operations.
"""

import os
import json
import tempfile
import shutil
from typing import Any, Dict
from datetime import datetime


# Exit codes
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_NETWORK_ERROR = 3
EXIT_VALIDATION_ERROR = 4


def atomic_write(filepath: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Write content to a file atomically using temp file + rename.
    
    This prevents partial writes and race conditions.
    
    Args:
        filepath: Target file path
        content: Content to write
        encoding: File encoding (default: utf-8)
    """
    directory = os.path.dirname(filepath) or '.'
    
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Write to temp file in same directory (ensures same filesystem)
    fd, temp_path = tempfile.mkstemp(dir=directory, text=True)
    try:
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Atomic rename (on POSIX systems)
        # On Windows, need to remove target first if it exists
        if os.name == 'nt' and os.path.exists(filepath):
            os.remove(filepath)
        
        shutil.move(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def safe_read_json(filepath: str, default: Any = None) -> Any:
    """
    Safely read and parse a JSON file.
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
    
    Returns:
        Parsed JSON data or default value
    """
    if not os.path.exists(filepath):
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def safe_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Safely write data to a JSON file atomically.
    
    Args:
        filepath: Target file path
        data: Data to serialize
        indent: JSON indentation level
    """
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(filepath, content)


def get_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.utcnow().isoformat() + 'Z'


def sanitize_string(s: str, max_length: int = 1000) -> str:
    """
    Sanitize a string for safe logging/storage.
    
    Args:
        s: Input string
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(s, str):
        s = str(s)
    
    # Truncate if too long
    if len(s) > max_length:
        s = s[:max_length] + '...'
    
    # Remove control characters except newlines/tabs
    s = ''.join(char for char in s if char.isprintable() or char in '\n\t')
    
    return s


def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def get_cache_dir() -> str:
    """
    Get the default cache directory for the application.
    
    Returns:
        Path to cache directory
    """
    # Use platform-specific cache location
    if os.name == 'nt':  # Windows
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        cache_dir = os.path.join(base, 'weather-harvester', 'cache')
    else:  # Unix-like
        base = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
        cache_dir = os.path.join(base, 'weather-harvester')
    
    ensure_dir(cache_dir)
    return cache_dir


def get_log_dir() -> str:
    """
    Get the default log directory for the application.
    
    Returns:
        Path to log directory
    """
    # Use platform-specific log location
    if os.name == 'nt':  # Windows
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(base, 'weather-harvester', 'logs')
    else:  # Unix-like
        base = os.path.expanduser('~/.local/share')
        log_dir = os.path.join(base, 'weather-harvester', 'logs')
    
    ensure_dir(log_dir)
    return log_dir


__all__ = [
    'EXIT_SUCCESS',
    'EXIT_GENERAL_ERROR',
    'EXIT_CONFIG_ERROR',
    'EXIT_NETWORK_ERROR',
    'EXIT_VALIDATION_ERROR',
    'atomic_write',
    'safe_read_json',
    'safe_write_json',
    'get_timestamp',
    'sanitize_string',
    'ensure_dir',
    'get_cache_dir',
    'get_log_dir',
]
