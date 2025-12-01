"""
File-based cache with TTL for Weather Harvester.

Provides thread-safe caching with time-to-live expiration.
"""

import os
import json
import hashlib
import threading
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from .logger import get_logger
from .utils import get_cache_dir, safe_read_json, safe_write_json, get_timestamp


logger = get_logger(__name__)


class Cache:
    """
    File-based JSON cache with TTL support.
    
    Each cache entry is stored as a separate JSON file with metadata
    including expiration time. Thread-safe with file locking.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            cache_dir: Directory for cache files (default: platform-specific)
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir or get_cache_dir()
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.debug(f"Cache initialized: {self.cache_dir} (TTL: {default_ttl}s)")
    
    def _get_cache_key(self, key: str) -> str:
        """
        Generate a cache key hash.
        
        Args:
            key: Original key string
        
        Returns:
            SHA256 hash of the key
        """
        return hashlib.sha256(key.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key.
        
        Args:
            key: Cache key
        
        Returns:
            Full path to cache file
        """
        cache_key = self._get_cache_key(key)
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache if not expired.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            data = safe_read_json(cache_path)
            
            if data is None:
                logger.debug(f"Cache miss: {key}")
                return None
            
            # Check expiration
            expires_at = data.get('expires_at')
            if expires_at:
                expiry_time = datetime.fromisoformat(expires_at.rstrip('Z'))
                if datetime.utcnow() > expiry_time:
                    logger.debug(f"Cache expired: {key}")
                    # Clean up expired entry
                    try:
                        os.remove(cache_path)
                    except OSError:
                        pass
                    return None
            
            logger.debug(f"Cache hit: {key}")
            return data.get('value')
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (default: use default_ttl)
        """
        cache_path = self._get_cache_path(key)
        ttl = ttl if ttl is not None else self.default_ttl
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        cache_data = {
            'key': key,
            'value': value,
            'created_at': get_timestamp(),
            'expires_at': expires_at.isoformat() + 'Z',
            'ttl': ttl,
        }
        
        with self._lock:
            try:
                safe_write_json(cache_path, cache_data)
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            except Exception as e:
                logger.error(f"Failed to write cache: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete a cache entry.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted, False if not found
        """
        cache_path = self._get_cache_path(key)
        
        with self._lock:
            if os.path.exists(cache_path):
                try:
                    os.remove(cache_path)
                    logger.debug(f"Cache deleted: {key}")
                    return True
                except OSError as e:
                    logger.error(f"Failed to delete cache: {e}")
                    return False
            return False
    
    def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries deleted
        """
        count = 0
        
        with self._lock:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(filepath)
                        count += 1
                    except OSError:
                        pass
        
        logger.info(f"Cache cleared: {count} entries deleted")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of expired entries deleted
        """
        count = 0
        now = datetime.utcnow()
        
        with self._lock:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                data = safe_read_json(filepath)
                
                if data:
                    expires_at = data.get('expires_at')
                    if expires_at:
                        expiry_time = datetime.fromisoformat(expires_at.rstrip('Z'))
                        if now > expiry_time:
                            try:
                                os.remove(filepath)
                                count += 1
                            except OSError:
                                pass
        
        logger.info(f"Cache cleanup: {count} expired entries deleted")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total = 0
        expired = 0
        total_size = 0
        now = datetime.utcnow()
        
        with self._lock:
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.cache_dir, filename)
                total += 1
                
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
                
                data = safe_read_json(filepath)
                if data:
                    expires_at = data.get('expires_at')
                    if expires_at:
                        expiry_time = datetime.fromisoformat(expires_at.rstrip('Z'))
                        if now > expiry_time:
                            expired += 1
        
        return {
            'total_entries': total,
            'expired_entries': expired,
            'valid_entries': total - expired,
            'total_size_bytes': total_size,
            'cache_dir': self.cache_dir,
        }


__all__ = ['Cache']
