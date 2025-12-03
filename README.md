  # Weather Harvester

  A resilient, production-grade Python CLI tool for fetching and monitoring weather data with intelligent caching, alerting, and a plugin architecture.

  ## Features

  - **🌦️ Weather Data Fetching**: Fetch current weather data using OpenWeatherMap API
  - **💾 Intelligent Caching**: File-based JSON cache with TTL to minimize API calls
  - **🔔 Smart Alerts**: Console and email alerts when weather thresholds are breached
  - **🔌 Plugin Architecture**: Extensible system for custom data processors and analyzers
  - **⚡ Concurrent Execution**: ThreadPoolExecutor support for parallel location monitoring
  - **📝 Structured Logging**: JSON logs with human-readable console output
  - **⚙️ Flexible Configuration**: INI and JSON config files with profile support
  - **🧪 Comprehensive Testing**: Unit tests with >80% coverage
  - **📦 Zero Dependencies**: Built entirely with Python standard library

  ## Installation

  ### From Source

  ```bash
  # Clone the repository
  cd weather_harvester

  # Install in development mode
  pip install -e .

  # Verify installation
  weather-harvester --version
  ```

  ### Requirements

  - Python 3.8 or higher
  - No external dependencies required!

  ## Quick Start

  ### 1. Configure API Key

  Edit `configs/example.ini` and add your OpenWeatherMap API key:

  ```ini
  [default]
  api_key = YOUR_API_KEY_HERE
  ```

  Get a free API key at: https://openweathermap.org/api

  ### 2. Fetch Weather Data

  ```bash
  # Fetch weather for a city
  python -m weather_harvester fetch --location "London"

  # Fetch using coordinates
  python -m weather_harvester fetch --location "40.7128,-74.0060"

  # Get JSON output
  python -m weather_harvester fetch --location "Paris" --output json
  ```

  ### 3. Monitor Continuously

  ```bash
  # Monitor a single location every 5 minutes
  python -m weather_harvester monitor --location "London" --interval 300


  # Monitor multiple locations in parallel
  python -m weather_harvester monitor --lat 51.5074 --lon -0.1278 --interval 300
  600 --parallel
  ```

  ## CLI Commands

  ### `fetch` - One-time Data Fetch

  Fetch weather data once and display results.

  ```bash
  weather-harvester fetch [OPTIONS]

  Options:
    --location, -l TEXT       Location (city name or "lat,lon")
    --no-cache               Bypass cache and fetch fresh data
    --output, -o [json|summary]  Output format (default: summary)
  ```

  **Examples:**

  ```bash
  # Basic fetch
  weather-harvester fetch --location "New York"

  # Force fresh data
  weather-harvester fetch --location "London" --no-cache

  # JSON output for scripting
  weather-harvester fetch --location "Tokyo" --output json
  ```

  ### `monitor` - Continuous Monitoring

  Monitor weather conditions and trigger alerts on threshold breaches.

  ```bash
  weather-harvester monitor [OPTIONS]

  Options:
    --locations, -l TEXT...  Locations to monitor
    --interval, -i INTEGER   Monitoring interval in seconds (default: 300)
    --parallel, -p          Fetch locations in parallel
  ```

  **Examples:**

  ```bash
  # Monitor single location
  weather-harvester monitor --locations "London" --interval 300

  # Monitor multiple locations in parallel
  weather-harvester monitor --locations "NYC" "LA" "Chicago" --parallel

  # Custom interval (every 10 minutes)
  weather-harvester monitor --locations "London" --interval 600
  ```

  ### `list-plugins` - Show Available Plugins

  List all discovered plugins.

  ```bash
  weather-harvester list-plugins
  ```

  ### `test-config` - Validate Configuration

  Test and validate configuration files.

  ```bash
  weather-harvester test-config [OPTIONS]

  Options:
    --config TEXT    Path to config file
    --profile TEXT   Profile to test
    --verbose, -v    Show all configuration values
  ```

  **Examples:**

  ```bash
  # Test default profile
  weather-harvester test-config

  # Test production profile
  weather-harvester test-config --profile prod --verbose
  ```

  ## Configuration

  ### Configuration Files

  Weather Harvester supports both INI and JSON configuration formats.

  **INI Format** (`configs/example.ini`):

  ```ini
  [default]
  api_key = YOUR_API_KEY_HERE
  cache_ttl = 300
  request_timeout = 10
  max_retries = 3
  alert_temperature_max = 35
  smtp_host = smtp.gmail.com
  smtp_to = alerts@example.com
  ```

  **JSON Format** (`configs/example.json`):

  ```json
  {
    "default": {
      "api_key": "YOUR_API_KEY_HERE",
      "cache_ttl": 300,
      "alert_temperature_max": 35
    }
  }
  ```

  ### Configuration Profiles

  Use profiles for different environments:

  - **default**: General use
  - **dev**: Development with verbose logging
  - **prod**: Production with optimized settings
  - **test**: Testing with minimal caching

  ```bash
  # Use development profile
  weather-harvester fetch --profile dev --location "London"

  # Use production profile
  weather-harvester monitor --profile prod --locations "NYC"
  ```

  ### Configuration Options

  | Option | Type | Default | Description |
  |--------|------|---------|-------------|
  | `api_url` | string | OpenWeatherMap URL | Weather API endpoint |
  | `api_key` | string | *required* | API authentication key |
  | `cache_ttl` | int | 300 | Cache time-to-live (seconds) |
  | `request_timeout` | int | 10 | HTTP request timeout (seconds) |
  | `max_retries` | int | 3 | Maximum retry attempts |
  | `retry_backoff` | float | 2.0 | Exponential backoff multiplier |
  | `alert_temperature_min` | float | -999 | Min temperature alert (°C) |
  | `alert_temperature_max` | float | 999 | Max temperature alert (°C) |
  | `alert_humidity_max` | int | 100 | Max humidity alert (%) |
  | `alert_wind_speed_max` | float | 999 | Max wind speed alert (m/s) |
  | `smtp_host` | string | "" | SMTP server hostname |
  | `smtp_port` | int | 587 | SMTP server port |
  | `smtp_user` | string | "" | SMTP username |
  | `smtp_password` | string | "" | SMTP password |
  | `smtp_from` | string | "" | Email sender address |
  | `smtp_to` | string | "" | Email recipient address |
  | `log_level` | string | INFO | Logging level |

  ## Plugin Development

  Create custom plugins to extend functionality.

  ### Plugin Interface

  ```python
  from weather_harvester.plugins.base import BasePlugin

  class MyPlugin(BasePlugin):
      @property
      def name(self) -> str:
          return "MyPlugin"
      
      @property
      def version(self) -> str:
          return "1.0.0"
      
      @property
      def description(self) -> str:
          return "My custom weather plugin"
      
      def process(self, data: dict) -> dict:
          # Transform or analyze weather data
          data['custom_field'] = "custom_value"
          return data
  ```

  ### Installing Plugins

  1. Create your plugin file in `src/weather_harvester/plugins/`
  2. Inherit from `BasePlugin`
  3. Implement required methods
  4. Plugins are auto-discovered on startup

  ### Example Plugins

  **Temperature Converter** - Converts Kelvin to Celsius/Fahrenheit and categorizes temperature ranges.

  **Weather Analyzer** - Analyzes conditions and provides insights (humidity, wind, visibility).

  ## Testing

  Run the comprehensive test suite:

  ```bash
  # Run all tests
  python -m unittest discover -s tests -v

  # Run specific test module
  python -m unittest tests.test_cache
  python -m unittest tests.test_config
  python -m unittest tests.test_fetcher

  # Run with coverage (if coverage.py installed)
  coverage run -m unittest discover -s tests
  coverage report
  ```

  ## Project Structure

  ```
  weather_harvester/
  ├── src/weather_harvester/
  │   ├── __init__.py          # Package initialization
  │   ├── __main__.py          # Module entry point
  │   ├── cli.py               # CLI interface
  │   ├── config.py            # Configuration management
  │   ├── cache.py             # Caching system
  │   ├── fetcher.py           # HTTP fetcher with retry
  │   ├── alerts.py            # Alert system
  │   ├── logger.py            # Structured logging
  │   ├── utils.py             # Utility functions
  │   └── plugins/
  │       ├── __init__.py      # Plugin discovery
  │       ├── base.py          # Base plugin interface
  │       └── sample_plugin.py # Example plugins
  ├── tests/
  │   ├── test_cache.py        # Cache tests
  │   ├── test_config.py       # Config tests
  │   └── test_fetcher.py      # Fetcher tests
  ├── configs/
  │   ├── example.ini          # Example INI config
  │   └── example.json         # Example JSON config
  ├── pyproject.toml           # Modern packaging config
  ├── setup.py                 # Legacy packaging support
  ├── LICENSE                  # MIT License
  └── README.md                # This file
  ```

  ## Logging

  Weather Harvester provides dual logging:

  - **Console**: Human-readable with ANSI colors
  - **File**: Structured JSON logs for parsing

  Logs are stored in platform-specific locations:
  - **Windows**: `%LOCALAPPDATA%\weather-harvester\logs\`
  - **Linux/Mac**: `~/.local/share/weather-harvester/`

  Control log level:

  ```bash
  weather-harvester --log-level DEBUG fetch --location "London"
  ```

  ## Caching

  Cache is stored in platform-specific locations:
  - **Windows**: `%LOCALAPPDATA%\weather-harvester\cache\`
  - **Linux/Mac**: `~/.cache/weather-harvester/`

  Each cache entry includes:
  - Original request parameters
  - Response data
  - Creation timestamp
  - Expiration time

  Cache is automatically cleaned up when expired entries are accessed.

  ## Alerts

  ### Console Alerts

  Automatically displayed when thresholds are breached:

  ```
  ⚠ WEATHER ALERT
  Location: London
  Time: 2025-11-30 08:00:00 UTC

    • Temperature too high: 36.5°C (threshold: 35°C)
    • Humidity too high: 92% (threshold: 90%)
  ```

  ### Email Alerts

  Configure SMTP settings in your config file:

  ```ini
  [prod]
  smtp_host = smtp.gmail.com
  smtp_port = 587
  smtp_user = your-email@gmail.com
  smtp_password = your-app-password
  smtp_from = your-email@gmail.com
  smtp_to = alerts@example.com
  ```

  Alerts include cooldown period (15 minutes) to prevent spam.

  ## Troubleshooting

  ### API Key Issues

  ```
  ERROR: Invalid API key
  ```

  **Solution**: Verify your API key in the config file and ensure it's active at OpenWeatherMap.

  ### Cache Issues

  ```
  ERROR: Failed to write cache
  ```

  **Solution**: Check write permissions for the cache directory or specify a custom cache directory in config.

  ### Network Errors

  ```
  ERROR: Failed to fetch data after 3 attempts
  ```

  **Solution**: Check internet connection, verify API endpoint, or increase `max_retries` in config.

  ## License

  MIT License - see [LICENSE](LICENSE) file for details.

  ## Contributing

  Contributions are welcome! Areas for enhancement:

  - Additional weather data sources
  - More sophisticated alert rules
  - Async/await implementation
  - Additional output formats (CSV, XML)
  - Database backend for cache
  - Web dashboard

  ## Acknowledgments

  - Weather data provided by [OpenWeatherMap](https://openweathermap.org/)
  - Built with Python standard library only
  - Inspired by production monitoring tools

  ---

  **Made with ❤️ for reliable weather monitoring**
