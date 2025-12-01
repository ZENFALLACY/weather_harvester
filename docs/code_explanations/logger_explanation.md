# logger.py - Code Explanation

## Overview

The `logger.py` module implements a dual-output logging system with structured JSON logs for machine parsing and human-readable colored console output.

## Module Structure

```python
weather_harvester/logger.py
├── JSONFormatter (Class)
├── HumanReadableFormatter (Class)
├── setup_logger() (Function)
└── get_logger() (Function)
```

---

## JSONFormatter Class

### Purpose
Custom logging formatter that outputs structured JSON for machine parsing and log aggregation tools.

### JSON Structure
```json
{
  "timestamp": "2025-11-30T08:30:45.123456Z",
  "level": "INFO",
  "logger": "weather_harvester.fetcher",
  "module": "fetcher",
  "function": "fetch",
  "line": 142,
  "message": "Successfully fetched weather data",
  "exception": "..." // Optional, if exception occurred
}
```

### Key Features

**1. Structured Data**
- Every log entry is valid JSON
- Consistent schema across all logs
- Easy to parse with jq, grep, or log aggregators

**2. Rich Context**
- Module and function name
- Line number
- Timestamp in ISO 8601 format

**3. Exception Handling**
- Automatically includes stack traces
- Formatted exception info in JSON

### Implementation Details

```python
def format(self, record: logging.LogRecord) -> str:
    log_data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': record.levelname,
        'logger': record.name,
        'module': record.module,
        'function': record.funcName,
        'line': record.lineno,
        'message': record.getMessage(),
    }
    
    if record.exc_info:
        log_data['exception'] = self.formatException(record.exc_info)
    
    return json.dumps(log_data, ensure_ascii=False)
```

### Use Cases
- Log aggregation (ELK, Splunk)
- Automated log analysis
- Debugging production issues
- Metrics extraction

---

## HumanReadableFormatter Class

### Purpose
Formatter for human-readable console output with ANSI color codes for better visibility.

### Color Scheme

| Level | Color | ANSI Code |
|-------|-------|-----------|
| DEBUG | Cyan | `\033[36m` |
| INFO | Green | `\033[32m` |
| WARNING | Yellow | `\033[33m` |
| ERROR | Red | `\033[31m` |
| CRITICAL | Magenta | `\033[35m` |

### Format Pattern
```
YYYY-MM-DD HH:MM:SS [LEVEL] logger_name: message
```

Example:
```
2025-11-30 08:30:45 [INFO] weather_harvester.fetcher: Successfully fetched weather data
```

### Smart Color Detection

```python
def __init__(self, use_colors: bool = True):
    self.use_colors = use_colors and sys.stderr.isatty()
```

**Logic:**
- Only use colors if output is a terminal (TTY)
- Automatically disabled when piping to files
- Prevents ANSI codes in log files

### Why stderr?
- Separates logs from program output
- Standard practice for logging
- Allows output redirection: `program > output.txt 2> errors.log`

---

## setup_logger() Function

### Purpose
Configure and initialize a logger with both console and file handlers.

### Parameters

```python
def setup_logger(
    name: str = 'weather_harvester',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    json_logs: bool = True,
    console_output: bool = True
) -> logging.Logger
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | str | 'weather_harvester' | Logger name |
| level | str | 'INFO' | Log level |
| log_file | str | Auto-generated | Log file path |
| json_logs | bool | True | Use JSON format for files |
| console_output | bool | True | Enable console output |

### Setup Flow

```
1. Create/get logger by name
   ↓
2. Check if already configured (avoid duplicates)
   ↓
3. Set log level
   ↓
4. Add console handler (if enabled)
   │  └─ HumanReadableFormatter with colors
   ↓
5. Add file handler
   │  ├─ Auto-generate filename if not provided
   │  └─ JSONFormatter or HumanReadableFormatter
   ↓
6. Disable propagation to root logger
   ↓
7. Return configured logger
```

### Dual Output Example

**Console (colored, human-readable):**
```
2025-11-30 08:30:45 [INFO] weather_harvester: Cache hit for London
```

**File (JSON, structured):**
```json
{"timestamp": "2025-11-30T08:30:45Z", "level": "INFO", "message": "Cache hit for London"}
```

### Auto-generated Log Filename

```python
timestamp = datetime.now().strftime('%Y%m%d')
log_file = os.path.join(log_dir, f'weather_harvester_{timestamp}.log')
```

Example: `weather_harvester_20251130.log`

**Benefits:**
- Daily log rotation
- Easy to find logs by date
- Prevents single huge log file

---

## get_logger() Function

### Purpose
Get or create a logger instance with lazy initialization.

### Usage Pattern

```python
# At module level
logger = get_logger(__name__)

# In functions
logger.info("Fetching weather data")
logger.error("Failed to connect")
```

### Lazy Setup
```python
def get_logger(name: str = 'weather_harvester') -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
```

**Logic:**
- If logger already configured → return it
- If not configured → set up with defaults
- Prevents duplicate handler registration

---

## Design Patterns

### 1. Dual Output Pattern
**Problem:** Need both human-readable and machine-parseable logs  
**Solution:** Two handlers with different formatters

```python
# Console handler - human-readable
console_handler.setFormatter(HumanReadableFormatter())

# File handler - JSON
file_handler.setFormatter(JSONFormatter())
```

### 2. Singleton Logger
**Problem:** Multiple logger instances cause duplicate logs  
**Solution:** Check for existing handlers before setup

```python
if logger.handlers:
    return logger  # Already configured
```

### 3. Smart Defaults
**Problem:** Users shouldn't need to configure everything  
**Solution:** Sensible defaults with override options

```python
level: str = 'INFO'          # Good default for production
json_logs: bool = True       # Enable structured logging
console_output: bool = True  # Show logs in terminal
```

---

## Thread Safety

### Built-in Thread Safety
Python's `logging` module is thread-safe by default:
- Handlers use locks internally
- Safe to call from multiple threads
- No additional synchronization needed

### Usage in Concurrent Code
```python
# Safe in ThreadPoolExecutor
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(fetch_weather, loc) for loc in locations]
    # Each thread can safely call logger.info()
```

---

## Log Levels

### When to Use Each Level

**DEBUG** - Detailed diagnostic information
```python
logger.debug(f"Cache key: {cache_key}")
logger.debug(f"Retry attempt {attempt}/{max_retries}")
```

**INFO** - Confirmation that things are working
```python
logger.info("Successfully fetched weather data")
logger.info(f"Loaded configuration from {config_file}")
```

**WARNING** - Something unexpected but recoverable
```python
logger.warning("Cache expired, fetching fresh data")
logger.warning(f"HTTP 500 error - retrying...")
```

**ERROR** - Serious problem, operation failed
```python
logger.error("Invalid API key")
logger.error(f"Failed to parse JSON: {e}")
```

**CRITICAL** - Very serious error, program may crash
```python
logger.critical("Cannot write to log directory")
```

---

## Performance Considerations

### Lazy Formatting
```python
# Good - only formats if level enabled
logger.debug("Cache key: %s", cache_key)

# Bad - always formats even if DEBUG disabled
logger.debug(f"Cache key: {cache_key}")
```

### File I/O Buffering
- File handlers use buffering by default
- Logs written in batches, not line-by-line
- Improves performance for high-volume logging

---

## Configuration Examples

### Development Setup
```python
logger = setup_logger(
    level='DEBUG',           # Verbose logging
    json_logs=False,         # Human-readable files
    console_output=True      # Show in terminal
)
```

### Production Setup
```python
logger = setup_logger(
    level='WARNING',         # Only warnings and errors
    json_logs=True,          # Structured for parsing
    console_output=False     # Silent operation
)
```

### Testing Setup
```python
logger = setup_logger(
    level='ERROR',           # Minimal noise
    log_file='/dev/null',    # Discard logs
    console_output=False     # Silent
)
```

---

## Common Issues & Solutions

### Issue: Duplicate Log Messages
**Cause:** Logger configured multiple times  
**Solution:** Check for existing handlers
```python
if logger.handlers:
    return logger
```

### Issue: No Color in Output
**Cause:** Output redirected to file or pipe  
**Solution:** Color detection with `isatty()`
```python
self.use_colors = use_colors and sys.stderr.isatty()
```

### Issue: Logs Not Appearing
**Cause:** Log level too high  
**Solution:** Check and adjust level
```python
logger.setLevel('DEBUG')  # Show all logs
```

---

## Integration with CLI

### CLI Log Level Control
```python
# In cli.py
logger = setup_logger(level=args.log_level)

# Command line
weather-harvester --log-level DEBUG fetch --location London
```

### Verbose Mode
```python
if args.verbose:
    logger.setLevel('DEBUG')
```

---

## Best Practices

1. **Use module-level loggers**
   ```python
   logger = get_logger(__name__)
   ```

2. **Include context in messages**
   ```python
   logger.info(f"Fetching weather for {location}")
   ```

3. **Log exceptions with context**
   ```python
   try:
       fetch_data()
   except Exception as e:
       logger.error(f"Failed to fetch: {e}")
   ```

4. **Use appropriate log levels**
   - Don't log everything as ERROR
   - Use DEBUG for diagnostic info
   - INFO for normal operations

5. **Avoid logging sensitive data**
   ```python
   # Bad
   logger.info(f"API key: {api_key}")
   
   # Good
   logger.info("API key configured")
   ```

---

## Future Enhancements

Potential improvements:
- Log rotation by size (not just date)
- Remote logging (syslog, HTTP)
- Custom log filters
- Structured logging with extra fields
- Performance metrics logging
