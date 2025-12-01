"""
Configuration management for Weather Harvester.

Supports INI and JSON config files with profile-based configurations.
"""

import os
import json
import configparser
from typing import Dict, Any, Optional
from .logger import get_logger
from .utils import EXIT_CONFIG_ERROR


logger = get_logger(__name__)


class Config:
    """
    Configuration manager supporting INI and JSON formats with profiles.
    
    Profiles allow different configurations for dev/prod/test environments.
    """
    
    # Default configuration values
    DEFAULTS = {
        'api_url': 'https://api.openweathermap.org/data/2.5/weather',
        'api_key': '',
        'cache_ttl': 300,  # 5 minutes
        'cache_dir': '',  # Will use platform default
        'request_timeout': 10,
        'max_retries': 3,
        'retry_backoff': 2.0,
        'alert_temperature_min': -999,
        'alert_temperature_max': 999,
        'alert_humidity_max': 100,
        'alert_wind_speed_max': 999,
        'smtp_host': '',
        'smtp_port': 587,
        'smtp_user': '',
        'smtp_password': '',
        'smtp_from': '',
        'smtp_to': '',
        'log_level': 'INFO',
        'log_file': '',
    }
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration.
        
        Args:
            config_data: Configuration dictionary (optional)
        """
        self._data = self.DEFAULTS.copy()
        if config_data:
            self._data.update(config_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._data[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration data.
        
        Returns:
            Dictionary of all configuration values
        """
        return self._data.copy()
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if valid, False otherwise
        """
        errors = []
        
        # Check required fields
        if not self._data.get('api_key'):
            errors.append("API key is required")
        
        # Validate numeric ranges
        if self._data.get('cache_ttl', 0) < 0:
            errors.append("cache_ttl must be non-negative")
        
        if self._data.get('request_timeout', 0) <= 0:
            errors.append("request_timeout must be positive")
        
        if self._data.get('max_retries', 0) < 0:
            errors.append("max_retries must be non-negative")
        
        # Log errors
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        
        logger.info("Configuration validation successful")
        return True


def load_config_from_ini(filepath: str, profile: str = 'default') -> Config:
    """
    Load configuration from an INI file.
    
    Args:
        filepath: Path to INI file
        profile: Configuration profile/section name
    
    Returns:
        Config instance
    
    Raises:
        SystemExit: If file not found or profile missing
    """
    if not os.path.exists(filepath):
        logger.error(f"Configuration file not found: {filepath}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    parser = configparser.ConfigParser()
    
    try:
        parser.read(filepath, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to parse INI file: {e}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    if profile not in parser:
        logger.error(f"Profile '{profile}' not found in {filepath}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    # Convert INI section to dict
    config_data = {}
    for key, value in parser[profile].items():
        # Try to convert to appropriate type
        config_data[key] = _parse_value(value)
    
    logger.info(f"Loaded configuration from {filepath} (profile: {profile})")
    return Config(config_data)


def load_config_from_json(filepath: str, profile: str = 'default') -> Config:
    """
    Load configuration from a JSON file.
    
    Args:
        filepath: Path to JSON file
        profile: Configuration profile name
    
    Returns:
        Config instance
    
    Raises:
        SystemExit: If file not found or profile missing
    """
    if not os.path.exists(filepath):
        logger.error(f"Configuration file not found: {filepath}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse JSON file: {e}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    if profile not in data:
        logger.error(f"Profile '{profile}' not found in {filepath}")
        raise SystemExit(EXIT_CONFIG_ERROR)
    
    logger.info(f"Loaded configuration from {filepath} (profile: {profile})")
    return Config(data[profile])


def load_config(filepath: str, profile: str = 'default') -> Config:
    """
    Load configuration from a file (auto-detect format).
    
    Args:
        filepath: Path to config file (.ini or .json)
        profile: Configuration profile name
    
    Returns:
        Config instance
    """
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.json':
        return load_config_from_json(filepath, profile)
    elif ext in ('.ini', '.cfg', '.conf'):
        return load_config_from_ini(filepath, profile)
    else:
        logger.error(f"Unsupported config file format: {ext}")
        raise SystemExit(EXIT_CONFIG_ERROR)


def _parse_value(value: str) -> Any:
    """
    Parse a string value to appropriate Python type.
    
    Args:
        value: String value
    
    Returns:
        Parsed value (int, float, bool, or str)
    """
    # Try boolean
    if value.lower() in ('true', 'yes', '1'):
        return True
    if value.lower() in ('false', 'no', '0'):
        return False
    
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value


__all__ = [
    'Config',
    'load_config',
    'load_config_from_ini',
    'load_config_from_json',
]
