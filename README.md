# Weather Harvester

A lightweight, modular Python tool that fetches real-time weather data, caches results for offline use, and provides a clean command-line interface — built using only Python’s Standard Library.

## Features

- Real-time Weather Fetching
  - Uses `urllib.request` to call public weather APIs
  - Parses responses using Python’s built-in `json` module
- Built-in Caching System
  - Saves weather results locally in JSON format
  - Automatically falls back to cache during network failure
- Configuration Support
  - Supports both INI (`configparser`) and JSON configuration files
  - Store API keys, default city, and caching preferences
- CLI Interface
  - Built using `argparse`
  - Supports city selection, forced refresh, showing cache, and config usage
- Robust Error Handling
  - Custom exception classes
  - Graceful recovery from network errors, invalid inputs, and API failures
- Structured Logging
  - JSON-formatted logging using Python’s `logging` module
  - Logs include errors, cache hits, API requests, and CLI commands
- Unit Testing
  - Test coverage using the `unittest` framework with network mocks and config/cache tests

## Project Structure

```
weather_harvester/
│── config/
│   ├── settings.ini
│   └── profiles.json
│
│── cache/
│   └── weather_cache.json
│
│── logs/
│   └── app.log
│
│── src/
│   ├── main.py            # Entrypoint
│   ├── cli.py             # Argument parsing
│   ├── fetcher.py         # Weather API calls
│   ├── cache_manager.py   # Cache read/write
│   ├── config_loader.py   # INI/JSON config handling
│   ├── logger.py          # Logging utilities
│   ├── exceptions.py      # Custom errors
│
│── tests/
│   ├── test_fetcher.py
│   ├── test_cache.py
│   ├── test_config.py
│   ├── test_cli.py
│
└── README.md
```

## Installation

No external libraries are required — the tool uses only the Python Standard Library.

Clone the repository:

```bash
git clone https://github.com/<username>/weather-harvester.git
cd weather-harvester
```

Ensure you have Python 3.8+ installed.

## Quick Usage

Fetch weather for a city:

```bash
python src/main.py --city Delhi
```

Use a configuration file:

```bash
python src/main.py --config config/settings.ini
```

Force-refresh and ignore cache:

```bash
python src/main.py --city Mumbai --refresh
```

Show cached data:

```bash
python src/main.py --use-cache
```

## Example Output

```
Weather Report for: Delhi
---------------------------------
Temperature : 27°C
Humidity    : 61%
Condition   : Clear Sky
Cache Used  : No
```

## Configuration

Example `config/settings.ini`:

```ini
[app]
default_city = Delhi
cache_enabled = true

[api]
base_url = http://api.weatherapi.com/v1/current.json
api_key = YOUR_API_KEY
```

Example `config/profiles.json`:

```json
{
  "profiles": {
    "default": {
      "city": "Mumbai",
      "cache": true
    },
    "work": {
      "city": "Bangalore",
      "cache": false
    }
  }
}
```

## Logging

Logs are written in JSON format to `logs/app.log`. The logger captures:

- CLI commands
- Outgoing API requests
- Cache hits/misses
- Errors and stack traces

## Testing

Run tests with the standard library's `unittest`:

```bash
python -m unittest discover tests
```

Tests include mocked network calls, config parsing, and cache read/write behavior.

## Development Notes

- The cache is stored at `cache/weather_cache.json` as a plain JSON file for easy inspection.
- Config loader supports both INI and JSON — the CLI prefers an explicit `--config` file, otherwise it falls back to defaults (`config/settings.ini` then `config/profiles.json`).

## Future Improvements

- Async weather fetching using `asyncio` for faster concurrent requests
- Support multiple weather service providers with automatic failover
- Package as a proper CLI (`setup.py` / `pyproject.toml`) to expose `weather-harvester` command
- Optional GUI using `tkinter`

## License

Choose a license for your project (e.g. MIT) and add a `LICENSE` file.

---

If you want, I can also:
- Add a `requirements.txt` (empty) or `pyproject.toml` for packaging notes
- Implement a basic `src/main.py` skeleton and some unit tests
- Add a short `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md`

Which of these would you like next?
