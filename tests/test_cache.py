"""
Unit tests for the cache module.
"""

import unittest
import os
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from weather_harvester.cache import Cache


class TestCache(unittest.TestCase):
    """Test cases for the Cache class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.cache = Cache(cache_dir=self.temp_dir, default_ttl=2)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        # Set value
        self.cache.set(key, value)
        
        # Get value
        retrieved = self.cache.get(key)
        self.assertEqual(retrieved, value)
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)
    
    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        key = "expiring_key"
        value = "expiring_value"
        
        # Set with 1 second TTL
        self.cache.set(key, value, ttl=1)
        
        # Should be available immediately
        self.assertEqual(self.cache.get(key), value)
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired now
        self.assertIsNone(self.cache.get(key))
    
    def test_cache_delete(self):
        """Test cache deletion."""
        key = "delete_key"
        value = "delete_value"
        
        self.cache.set(key, value)
        self.assertEqual(self.cache.get(key), value)
        
        # Delete
        result = self.cache.delete(key)
        self.assertTrue(result)
        
        # Should be gone
        self.assertIsNone(self.cache.get(key))
        
        # Deleting again should return False
        result = self.cache.delete(key)
        self.assertFalse(result)
    
    def test_cache_clear(self):
        """Test clearing all cache entries."""
        # Add multiple entries
        for i in range(5):
            self.cache.set(f"key_{i}", f"value_{i}")
        
        # Clear cache
        count = self.cache.clear()
        self.assertEqual(count, 5)
        
        # All should be gone
        for i in range(5):
            self.assertIsNone(self.cache.get(f"key_{i}"))
    
    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        # Add entries with different TTLs
        self.cache.set("short_ttl", "value1", ttl=1)
        self.cache.set("long_ttl", "value2", ttl=10)
        
        # Wait for short TTL to expire
        time.sleep(1.5)
        
        # Cleanup
        count = self.cache.cleanup_expired()
        self.assertEqual(count, 1)
        
        # Short TTL should be gone
        self.assertIsNone(self.cache.get("short_ttl"))
        
        # Long TTL should still exist
        self.assertEqual(self.cache.get("long_ttl"), "value2")
    
    def test_cache_stats(self):
        """Test cache statistics."""
        # Add some entries
        self.cache.set("key1", "value1", ttl=10)
        self.cache.set("key2", "value2", ttl=1)
        
        # Wait for one to expire
        time.sleep(1.5)
        
        # Get stats
        stats = self.cache.get_stats()
        
        self.assertEqual(stats['total_entries'], 2)
        self.assertEqual(stats['expired_entries'], 1)
        self.assertEqual(stats['valid_entries'], 1)
        self.assertGreater(stats['total_size_bytes'], 0)
        self.assertEqual(stats['cache_dir'], self.temp_dir)
    
    def test_cache_key_hashing(self):
        """Test that different keys produce different cache files."""
        key1 = "location:London"
        key2 = "location:Paris"
        
        self.cache.set(key1, "data1")
        self.cache.set(key2, "data2")
        
        # Both should be retrievable
        self.assertEqual(self.cache.get(key1), "data1")
        self.assertEqual(self.cache.get(key2), "data2")
        
        # Should create 2 files
        cache_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.json')]
        self.assertEqual(len(cache_files), 2)
    
    def test_cache_complex_data(self):
        """Test caching complex nested data structures."""
        complex_data = {
            "location": "London",
            "weather": {
                "temp": 20.5,
                "conditions": ["cloudy", "windy"]
            },
            "metadata": {
                "timestamp": "2025-01-01T00:00:00Z",
                "source": "test"
            }
        }
        
        self.cache.set("complex", complex_data)
        retrieved = self.cache.get("complex")
        
        self.assertEqual(retrieved, complex_data)


if __name__ == '__main__':
    unittest.main()
