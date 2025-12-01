"""
HTTP fetcher with retry logic for Weather Harvester.

Uses urllib for HTTP requests with exponential backoff and caching.
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Dict, Any, Optional
from .logger import get_logger
from .cache import Cache
from .config import Config
from .utils import EXIT_NETWORK_ERROR


logger = get_logger(__name__)


class WeatherFetcher:
    """
    Weather data fetcher with retry logic and caching.
    
    Uses urllib for HTTP requests and integrates with the cache layer
    to minimize API calls.
    """
    
    def __init__(self, config: Config, cache: Optional[Cache] = None):
        """
        Initialize fetcher.
        
        Args:
            config: Configuration instance
            cache: Cache instance (optional)
        """
        self.config = config
        self.cache = cache or Cache(
            default_ttl=config.get('cache_ttl', 300)
        )
        
        self.api_url = config.get('api_url')
        self.api_key = config.get('api_key')
        self.timeout = config.get('request_timeout', 10)
        self.max_retries = config.get('max_retries', 3)
        self.retry_backoff = config.get('retry_backoff', 2.0)
    
    def _build_cache_key(self, location: str, params: Dict[str, Any]) -> str:
        """
        Build a cache key from request parameters.
        
        Args:
            location: Location string (lat,lon or city name)
            params: Additional query parameters
        
        Returns:
            Cache key string
        """
        # Sort params for consistent keys
        sorted_params = sorted(params.items())
        param_str = '&'.join(f"{k}={v}" for k, v in sorted_params)
        return f"{location}:{param_str}"
    
    def _parse_location(self, location: str) -> Dict[str, str]:
        """
        Parse location string into query parameters.
        
        Args:
            location: Location string (e.g., "40.7128,-74.0060" or "London")
        
        Returns:
            Dictionary with 'lat'/'lon' or 'q' parameter
        """
        # Check if it's lat,lon format
        if ',' in location:
            try:
                lat, lon = location.split(',', 1)
                lat = lat.strip()
                lon = lon.strip()
                # Validate numeric
                float(lat)
                float(lon)
                return {'lat': lat, 'lon': lon}
            except ValueError:
                pass
        
        # Treat as city name
        return {'q': location}
    
    def fetch(
        self,
        location: str,
        use_cache: bool = True,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fetch weather data for a location.
        
        Args:
            location: Location string (lat,lon or city name)
            use_cache: Whether to use cached data
            extra_params: Additional query parameters
        
        Returns:
            Weather data dictionary
        
        Raises:
            SystemExit: On network errors after retries
        """
        # Build query parameters
        params = self._parse_location(location)
        params['appid'] = self.api_key
        
        if extra_params:
            params.update(extra_params)
        
        # Check cache first
        cache_key = self._build_cache_key(location, params)
        
        if use_cache:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached data for {location}")
                return cached_data
        
        # Fetch from API with retries
        data = self._fetch_with_retry(params)
        
        # Cache the result
        if use_cache:
            self.cache.set(cache_key, data)
        
        return data
    
    def _fetch_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch data with exponential backoff retry logic.
        
        Args:
            params: Query parameters
        
        Returns:
            Response data
        
        Raises:
            SystemExit: After max retries exceeded
        """
        url = f"{self.api_url}?{urllib.parse.urlencode(params)}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching data (attempt {attempt + 1}/{self.max_retries})")
                
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'WeatherHarvester/1.0')
                
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = response.read().decode('utf-8')
                    result = json.loads(data)
                    
                    logger.info(f"Successfully fetched weather data")
                    return result
            
            except urllib.error.HTTPError as e:
                # Handle HTTP errors
                error_msg = f"HTTP {e.code}: {e.reason}"
                
                if e.code == 401:
                    logger.error("Invalid API key")
                    raise SystemExit(EXIT_NETWORK_ERROR)
                elif e.code == 404:
                    logger.error(f"Location not found")
                    raise SystemExit(EXIT_NETWORK_ERROR)
                elif e.code >= 500:
                    # Server error - retry
                    logger.warning(f"{error_msg} - retrying...")
                else:
                    # Client error - don't retry
                    logger.error(error_msg)
                    raise SystemExit(EXIT_NETWORK_ERROR)
            
            except urllib.error.URLError as e:
                # Network error - retry
                logger.warning(f"Network error: {e.reason} - retrying...")
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                raise SystemExit(EXIT_NETWORK_ERROR)
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise SystemExit(EXIT_NETWORK_ERROR)
            
            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                sleep_time = self.retry_backoff ** attempt
                logger.debug(f"Waiting {sleep_time:.1f}s before retry")
                time.sleep(sleep_time)
        
        # Max retries exceeded
        logger.error(f"Failed to fetch data after {self.max_retries} attempts")
        raise SystemExit(EXIT_NETWORK_ERROR)


__all__ = ['WeatherFetcher']
