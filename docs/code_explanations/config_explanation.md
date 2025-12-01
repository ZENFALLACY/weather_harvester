# config.py - Code Explanation

## Overview

The `config.py` module manages application configuration with support for multiple file formats (INI/JSON) and profile-based configurations for different environments.

## Module Structure

```python
weather_harvester/config.py
├── Config (Class)
│   ├── DEFAULTS (dict)
│   ├── __init__()
│   ├── get()
│   ├── set()
│   ├── get_all()
│   └── validate()
├── load_config_from_ini()
├── load_config_from_json()
├── load_config()
└── _parse_value()
```

---

## Config Class

### Purpose
Container for configuration values with validation and default handling.

### Default Values

```python
DEFAULTS = {
    'api_url': 'https://api.openweathermap.org/data/2.5/weather',
    'api_key': '',
    'cache_ttl': 300,  # 5 minutes
    'request_timeout': 10,
    'max_retries': 3,
    'retry_backoff': 2.0,
    'alert_temperature_min': -999,
    'alert_temperature_max': 999,
    'alert_humidity_max': 100,
    'alert_wind_speed_max': 999,
    'smtp_host': '',
    'smtp_port': 587,
    'log_level': 'INFO',
    # ... more defaults
}
```

### Methods

**get(key, default=None)**
```python
config.get('cache_ttl')  # Returns 300
config.get('missing_key', 'fallback')  # Returns 'fallback'
```

**set(key, value)**
```python
config.set('cache_ttl', 600)  # Update value
```

**validate()**
```python
if config.validate():
    # Configuration is valid
else:
    # Validation failed, check logs
```

### Validation Rules

1. **API Key Required**
   ```python
   if not self._data.get('api_key'):
       errors.append("API key is required")
   ```

2. **Non-negative TTL**
   ```python
   if self._data.get('cache_ttl', 0) < 0:
       errors.append("cache_ttl must be non-negative")
   ```

3. **Positive Timeout**
   ```python
   if self._data.get('request_timeout', 0) <= 0:
       errors.append("request_timeout must be positive")
   ```

4. **Non-negative Retries**
   ```python
   if self._data.get('max_retries', 0) < 0:
       errors.append("max_retries must be non-negative")
   ```

---

## load_config_from_ini()

### Purpose
Load configuration from INI file with profile support.

### INI File Format

```ini
[default]
api_key = YOUR_API_KEY
cache_ttl = 300
log_level = INFO

[dev]
api_key = DEV_API_KEY
cache_ttl = 60
log_level = DEBUG

[prod]
api_key = PROD_API_KEY
cache_ttl = 600
log_level = WARNING
```

### Loading Process

```
1. Check file exists
   ↓
2. Parse INI file with configparser
   ↓
3. Check profile exists
   ↓
4. Extract profile section
   ↓
5. Parse values to correct types
   ↓
6. Create Config object
```

### Type Parsing

Values are automatically converted:
- `"true"` → `True` (boolean)
- `"300"` → `300` (integer)
- `"2.5"` → `2.5` (float)
- `"text"` → `"text"` (string)

---

## load_config_from_json()

### Purpose
Load configuration from JSON file with profile support.

### JSON File Format

```json
{
  "default": {
    "api_key": "YOUR_API_KEY",
    "cache_ttl": 300,
    "log_level": "INFO"
  },
  "dev": {
    "api_key": "DEV_API_KEY",
    "cache_ttl": 60,
    "log_level": "DEBUG"
  }
}
```

### Advantages of JSON
- Native type support (no parsing needed)
- Nested structures possible
- Easier for programmatic generation

---

## load_config()

### Purpose
Auto-detect format and load configuration.

### Format Detection

```python
ext = os.path.splitext(filepath)[1].lower()

if ext == '.json':
    return load_config_from_json(filepath, profile)
elif ext in ('.ini', '.cfg', '.conf'):
    return load_config_from_ini(filepath, profile)
else:
    # Error: unsupported format
```

### Usage

```python
# Auto-detects format
config = load_config('config.ini', 'dev')
config = load_config('config.json', 'prod')
```

---

## _parse_value() Helper

### Purpose
Convert string values to appropriate Python types.

### Parsing Logic

```python
def _parse_value(value: str) -> Any:
    # Boolean
    if value.lower() in ('true', 'yes', '1'):
        return True
    if value.lower() in ('false', 'no', '0'):
        return False
    
    # Integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Float
    try:
        return float(value)
    except ValueError:
        pass
    
    # String (fallback)
    return value
```

### Examples

```python
_parse_value("true")    # → True
_parse_value("300")     # → 300
_parse_value("2.5")     # → 2.5
_parse_value("London")  # → "London"
```

---

## Profile-Based Configuration

### Purpose
Different settings for different environments.

### Common Profiles

**default** - General use
```ini
[default]
cache_ttl = 300
log_level = INFO
```

**dev** - Development
```ini
[dev]
cache_ttl = 60        # Shorter cache
log_level = DEBUG     # Verbose logging
```

**prod** - Production
```ini
[prod]
cache_ttl = 600       # Longer cache
log_level = WARNING   # Less noise
max_retries = 5       # More resilient
```

**test** - Testing
```ini
[test]
cache_ttl = 30        # Minimal cache
log_level = ERROR     # Quiet
```

### Usage

```bash
# Use dev profile
weather-harvester --profile dev fetch --location London

# Use prod profile
weather-harvester --profile prod monitor
```

---

## Error Handling

### File Not Found

```python
if not os.path.exists(filepath):
    logger.error(f"Configuration file not found: {filepath}")
    raise SystemExit(EXIT_CONFIG_ERROR)
```

### Invalid Format

```python
try:
    parser.read(filepath, encoding='utf-8')
except Exception as e:
    logger.error(f"Failed to parse INI file: {e}")
    raise SystemExit(EXIT_CONFIG_ERROR)
```

### Missing Profile

```python
if profile not in parser:
    logger.error(f"Profile '{profile}' not found in {filepath}")
    raise SystemExit(EXIT_CONFIG_ERROR)
```

---

## Design Patterns

### 1. Defaults Pattern
Provide sensible defaults for all settings.

**Benefits:**
- Works out of the box
- Users only configure what they need
- Backward compatibility

### 2. Validation Pattern
Validate configuration before use.

**Benefits:**
- Fail fast with clear errors
- Prevent runtime issues
- Document requirements

### 3. Profile Pattern
Environment-specific configurations.

**Benefits:**
- Single config file for all environments
- Easy to switch between environments
- Consistent structure

---

## Best Practices

### 1. Sensitive Data

**Don't log sensitive values:**
```python
# Bad
logger.info(f"API key: {config.get('api_key')}")

# Good
logger.info("API key configured")
```

**Mask in output:**
```python
if 'password' in key.lower() or 'key' in key.lower():
    value = '***' if value else ''
```

### 2. Required vs Optional

**Required fields:**
```python
if not config.get('api_key'):
    raise ValueError("API key is required")
```

**Optional with defaults:**
```python
cache_ttl = config.get('cache_ttl', 300)  # Default: 300
```

### 3. Type Safety

**Validate types:**
```python
cache_ttl = config.get('cache_ttl')
if not isinstance(cache_ttl, int):
    raise TypeError("cache_ttl must be integer")
```

---

## Testing Considerations

### Temporary Config Files

```python
def test_load_ini():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini') as f:
        f.write("[default]\napi_key = test\n")
        f.flush()
        config = load_config_from_ini(f.name, 'default')
        assert config.get('api_key') == 'test'
```

### Mock File System

```python
@patch('os.path.exists')
def test_missing_file(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(SystemExit):
        load_config('missing.ini', 'default')
```

---

## Common Usage Patterns

### Load and Validate

```python
config = load_config('config.ini', 'prod')
if not config.validate():
    sys.exit(EXIT_CONFIG_ERROR)
```

### Override Specific Values

```python
config = load_config('config.ini', 'default')
config.set('cache_ttl', 600)  # Override for this run
```

### Environment-Specific Loading

```python
env = os.getenv('ENVIRONMENT', 'default')
config = load_config('config.ini', env)
```

---

## Configuration Reference

### API Settings
- `api_url` - Weather API endpoint
- `api_key` - API authentication key

### Cache Settings
- `cache_ttl` - Time-to-live in seconds
- `cache_dir` - Cache directory path

### Network Settings
- `request_timeout` - HTTP timeout (seconds)
- `max_retries` - Maximum retry attempts
- `retry_backoff` - Backoff multiplier

### Alert Settings
- `alert_temperature_min` - Min temp (°C)
- `alert_temperature_max` - Max temp (°C)
- `alert_humidity_max` - Max humidity (%)
- `alert_wind_speed_max` - Max wind (m/s)

### SMTP Settings
- `smtp_host` - SMTP server
- `smtp_port` - SMTP port
- `smtp_user` - Username
- `smtp_password` - Password
- `smtp_from` - Sender email
- `smtp_to` - Recipient email

### Logging Settings
- `log_level` - Log level
- `log_file` - Log file path

---

## Future Enhancements

Potential improvements:
- Environment variable interpolation
- Config file includes/imports
- Schema validation (JSON Schema)
- Hot reload on file change
- Encrypted sensitive values
- Remote config sources
