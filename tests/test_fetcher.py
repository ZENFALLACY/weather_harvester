"""
Unit tests for the fetcher module.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import json
import urllib.error
from weather_harvester.fetcher import WeatherFetcher
from weather_harvester.config import Config
from weather_harvester.cache import Cache


class TestWeatherFetcher(unittest.TestCase):
    """Test cases for the WeatherFetcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config({
            'api_url': 'https://api.example.com/weather',
            'api_key': 'test_api_key',
            'cache_ttl': 300,
            'request_timeout': 10,
            'max_retries': 3,
            'retry_backoff': 1.0
        })
        
        # Use a mock cache to avoid file I/O
        self.cache = Mock(spec=Cache)
        self.cache.get.return_value = None
        
        self.fetcher = WeatherFetcher(self.config, self.cache)
    
    def test_parse_location_latlon(self):
        """Test parsing lat,lon location format."""
        result = self.fetcher._parse_location("40.7128,-74.0060")
        self.assertEqual(result, {'lat': '40.7128', 'lon': '-74.0060'})
    
    def test_parse_location_city(self):
        """Test parsing city name location format."""
        result = self.fetcher._parse_location("London")
        self.assertEqual(result, {'q': 'London'})
    
    def test_build_cache_key(self):
        """Test cache key generation."""
        params = {'lat': '40.7128', 'lon': '-74.0060', 'appid': 'test_key'}
        key = self.fetcher._build_cache_key("40.7128,-74.0060", params)
        
        # Should be deterministic
        key2 = self.fetcher._build_cache_key("40.7128,-74.0060", params)
        self.assertEqual(key, key2)
        
        # Different location should produce different key
        key3 = self.fetcher._build_cache_key("London", params)
        self.assertNotEqual(key, key3)
    
    @patch('urllib.request.urlopen')
    def test_fetch_success(self, mock_urlopen):
        """Test successful weather data fetch."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'name': 'London',
            'main': {'temp': 293.15, 'humidity': 65},
            'weather': [{'description': 'cloudy'}]
        }).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Fetch data
        data = self.fetcher.fetch("London", use_cache=False)
        
        # Verify
        self.assertEqual(data['name'], 'London')
        self.assertEqual(data['main']['temp'], 293.15)
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_fetch_uses_cache(self, mock_urlopen):
        """Test that fetch uses cached data when available."""
        cached_data = {'name': 'London', 'cached': True}
        self.cache.get.return_value = cached_data
        
        # Fetch data
        data = self.fetcher.fetch("London", use_cache=True)
        
        # Should return cached data without making HTTP request
        self.assertEqual(data, cached_data)
        mock_urlopen.assert_not_called()
    
    @patch('urllib.request.urlopen')
    def test_fetch_bypasses_cache(self, mock_urlopen):
        """Test that fetch can bypass cache."""
        # Set up cache with data
        self.cache.get.return_value = {'cached': True}
        
        # Mock fresh response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'fresh': True}).encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        # Fetch with cache disabled
        data = self.fetcher.fetch("London", use_cache=False)
        
        # Should fetch fresh data
        self.assertEqual(data, {'fresh': True})
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_fetch_retry_on_server_error(self, mock_sleep, mock_urlopen):
        """Test retry logic on server errors."""
        # First two attempts fail with 500, third succeeds
        mock_urlopen.side_effect = [
            urllib.error.HTTPError('url', 500, 'Server Error', {}, None),
            urllib.error.HTTPError('url', 500, 'Server Error', {}, None),
            MagicMock(
                read=lambda: json.dumps({'success': True}).encode('utf-8'),
                __enter__=lambda self: self,
                __exit__=lambda *args: None
            )
        ]
        
        # Fetch should succeed after retries
        data = self.fetcher.fetch("London", use_cache=False)
        self.assertEqual(data, {'success': True})
        
        # Should have made 3 attempts
        self.assertEqual(mock_urlopen.call_count, 3)
    
    @patch('urllib.request.urlopen')
    def test_fetch_fails_on_401(self, mock_urlopen):
        """Test that 401 errors don't retry."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 401, 'Unauthorized', {}, None
        )
        
        # Should raise SystemExit without retrying
        with self.assertRaises(SystemExit):
            self.fetcher.fetch("London", use_cache=False)
        
        # Should only attempt once
        self.assertEqual(mock_urlopen.call_count, 1)
    
    @patch('urllib.request.urlopen')
    def test_fetch_fails_on_404(self, mock_urlopen):
        """Test that 404 errors don't retry."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 404, 'Not Found', {}, None
        )
        
        with self.assertRaises(SystemExit):
            self.fetcher.fetch("InvalidLocation", use_cache=False)
        
        self.assertEqual(mock_urlopen.call_count, 1)
    
    @patch('urllib.request.urlopen')
    @patch('time.sleep')
    def test_fetch_max_retries_exceeded(self, mock_sleep, mock_urlopen):
        """Test that fetch fails after max retries."""
        # All attempts fail
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 500, 'Server Error', {}, None
        )
        
        with self.assertRaises(SystemExit):
            self.fetcher.fetch("London", use_cache=False)
        
        # Should attempt max_retries times
        self.assertEqual(mock_urlopen.call_count, 3)
    
    @patch('urllib.request.urlopen')
    def test_fetch_invalid_json(self, mock_urlopen):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'invalid json{'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(SystemExit):
            self.fetcher.fetch("London", use_cache=False)


if __name__ == '__main__':
    unittest.main()
