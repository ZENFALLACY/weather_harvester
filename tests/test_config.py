"""
Unit tests for the config module.
"""

import unittest
import os
import tempfile
import json
from weather_harvester.config import Config, load_config_from_ini, load_config_from_json


class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""
    
    def test_config_defaults(self):
        """Test that default values are set correctly."""
        config = Config()
        
        self.assertEqual(config.get('cache_ttl'), 300)
        self.assertEqual(config.get('request_timeout'), 10)
        self.assertEqual(config.get('max_retries'), 3)
        self.assertEqual(config.get('log_level'), 'INFO')
    
    def test_config_get_set(self):
        """Test get and set operations."""
        config = Config()
        
        config.set('custom_key', 'custom_value')
        self.assertEqual(config.get('custom_key'), 'custom_value')
        
        # Test default value
        self.assertEqual(config.get('nonexistent', 'default'), 'default')
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = Config({
            'api_key': 'test_key',
            'cache_ttl': 300,
            'request_timeout': 10,
            'max_retries': 3
        })
        
        self.assertTrue(config.validate())
    
    def test_config_validation_missing_api_key(self):
        """Test validation fails with missing API key."""
        config = Config({'api_key': ''})
        self.assertFalse(config.validate())
    
    def test_config_validation_negative_ttl(self):
        """Test validation fails with negative TTL."""
        config = Config({
            'api_key': 'test_key',
            'cache_ttl': -1
        })
        self.assertFalse(config.validate())
    
    def test_config_validation_invalid_timeout(self):
        """Test validation fails with invalid timeout."""
        config = Config({
            'api_key': 'test_key',
            'request_timeout': 0
        })
        self.assertFalse(config.validate())


class TestConfigLoading(unittest.TestCase):
    """Test cases for configuration file loading."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_load_ini_config(self):
        """Test loading configuration from INI file."""
        # Create test INI file
        ini_path = os.path.join(self.temp_dir, 'test.ini')
        with open(ini_path, 'w') as f:
            f.write("""
[default]
api_key = test_api_key
cache_ttl = 600
request_timeout = 15
max_retries = 5
log_level = DEBUG

[dev]
api_key = dev_api_key
cache_ttl = 60
""")
        
        # Load default profile
        config = load_config_from_ini(ini_path, 'default')
        self.assertEqual(config.get('api_key'), 'test_api_key')
        self.assertEqual(config.get('cache_ttl'), 600)
        self.assertEqual(config.get('request_timeout'), 15)
        self.assertEqual(config.get('log_level'), 'DEBUG')
        
        # Load dev profile
        config_dev = load_config_from_ini(ini_path, 'dev')
        self.assertEqual(config_dev.get('api_key'), 'dev_api_key')
        self.assertEqual(config_dev.get('cache_ttl'), 60)
    
    def test_load_json_config(self):
        """Test loading configuration from JSON file."""
        # Create test JSON file
        json_path = os.path.join(self.temp_dir, 'test.json')
        config_data = {
            'default': {
                'api_key': 'test_api_key',
                'cache_ttl': 600,
                'request_timeout': 15,
                'max_retries': 5,
                'log_level': 'DEBUG'
            },
            'prod': {
                'api_key': 'prod_api_key',
                'cache_ttl': 1200
            }
        }
        
        with open(json_path, 'w') as f:
            json.dump(config_data, f)
        
        # Load default profile
        config = load_config_from_json(json_path, 'default')
        self.assertEqual(config.get('api_key'), 'test_api_key')
        self.assertEqual(config.get('cache_ttl'), 600)
        
        # Load prod profile
        config_prod = load_config_from_json(json_path, 'prod')
        self.assertEqual(config_prod.get('api_key'), 'prod_api_key')
        self.assertEqual(config_prod.get('cache_ttl'), 1200)
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises SystemExit."""
        with self.assertRaises(SystemExit):
            load_config_from_ini('/nonexistent/path.ini', 'default')
    
    def test_load_missing_profile(self):
        """Test loading missing profile raises SystemExit."""
        ini_path = os.path.join(self.temp_dir, 'test.ini')
        with open(ini_path, 'w') as f:
            f.write("[default]\napi_key = test\n")
        
        with self.assertRaises(SystemExit):
            load_config_from_ini(ini_path, 'nonexistent')
    
    def test_type_parsing(self):
        """Test that INI values are parsed to correct types."""
        ini_path = os.path.join(self.temp_dir, 'test.ini')
        with open(ini_path, 'w') as f:
            f.write("""
[default]
api_key = test_key
cache_ttl = 300
retry_backoff = 2.5
use_cache = true
disabled = false
""")
        
        config = load_config_from_ini(ini_path, 'default')
        
        # Check types
        self.assertIsInstance(config.get('cache_ttl'), int)
        self.assertEqual(config.get('cache_ttl'), 300)
        
        self.assertIsInstance(config.get('retry_backoff'), float)
        self.assertEqual(config.get('retry_backoff'), 2.5)
        
        self.assertIsInstance(config.get('use_cache'), bool)
        self.assertTrue(config.get('use_cache'))
        
        self.assertIsInstance(config.get('disabled'), bool)
        self.assertFalse(config.get('disabled'))


if __name__ == '__main__':
    unittest.main()
