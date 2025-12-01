# utils.py - Code Explanation

## Overview

The `utils.py` module provides shared utility functions and constants used throughout the Weather Harvester application. It focuses on atomic file operations, exit codes, and platform-specific directory handling.

## Module Structure

```python
weather_harvester/utils.py
├── Exit Codes (Constants)
├── File I/O Functions
├── JSON Helpers
├── Timestamp Utilities
├── String Sanitization
└── Directory Management
```

## Exit Codes

### Purpose
Standardized exit codes for shell scripting and automation.

### Constants
```python
EXIT_SUCCESS = 0           # Successful execution
EXIT_GENERAL_ERROR = 1     # General error
EXIT_CONFIG_ERROR = 2      # Configuration error
EXIT_NETWORK_ERROR = 3     # Network/API error
EXIT_VALIDATION_ERROR = 4  # Validation error
```

### Usage
```python
if not config.validate():
    sys.exit(EXIT_CONFIG_ERROR)
```

---

## atomic_write()

### Purpose
Write content to a file atomically to prevent partial writes and race conditions.

### How It Works
1. Creates a temporary file in the same directory as target
2. Writes content to temp file
3. Atomically renames temp file to target (on POSIX)
4. On Windows, removes target first if it exists

### Why Atomic?
- Prevents readers from seeing partial data
- Ensures all-or-nothing writes
- Safe for concurrent access

### Code Flow
```
1. Create temp file in same directory
   ↓
2. Write content to temp file
   ↓
3. Close temp file
   ↓
4. [Windows only] Remove target if exists
   ↓
5. Rename temp → target (atomic on POSIX)
```

### Example
```python
atomic_write('/path/to/cache.json', json_content)
# Guarantees readers never see partial JSON
```

---

## safe_read_json()

### Purpose
Safely read and parse JSON files with error handling.

### Parameters
- `filepath` - Path to JSON file
- `default` - Value to return on error (default: None)

### Error Handling
- File not found → returns default
- Invalid JSON → returns default
- I/O error → returns default

### Use Cases
- Reading cache files that may not exist
- Loading optional configuration
- Recovering from corrupted files

### Example
```python
cache_data = safe_read_json('cache.json', default={})
# Returns {} if file missing or invalid
```

---

## safe_write_json()

### Purpose
Safely write data to JSON file with atomic operation.

### Features
- Serializes data to JSON
- Uses atomic_write() for safety
- Configurable indentation
- UTF-8 encoding

### Parameters
- `filepath` - Target file path
- `data` - Data to serialize (must be JSON-serializable)
- `indent` - Indentation level (default: 2)

### Example
```python
safe_write_json('data.json', {'key': 'value'})
# Atomically writes formatted JSON
```

---

## get_timestamp()

### Purpose
Generate ISO 8601 formatted UTC timestamps.

### Format
`YYYY-MM-DDTHH:MM:SS.ffffffZ`

Example: `2025-11-30T08:30:45.123456Z`

### Why UTC?
- Consistent across timezones
- Standard for APIs and logs
- Avoids DST issues

### Usage
```python
timestamp = get_timestamp()
# "2025-11-30T08:30:45.123456Z"
```

---

## sanitize_string()

### Purpose
Clean strings for safe logging and storage.

### Operations
1. Convert to string if needed
2. Truncate if exceeds max_length
3. Remove control characters (except \n, \t)
4. Preserve printable characters

### Parameters
- `s` - Input string
- `max_length` - Maximum allowed length (default: 1000)

### Why Sanitize?
- Prevents log injection attacks
- Avoids terminal corruption
- Limits memory usage
- Removes invisible characters

### Example
```python
clean = sanitize_string(user_input, max_length=100)
# Safe for logging
```

---

## ensure_dir()

### Purpose
Ensure a directory exists, creating it if necessary.

### Features
- Creates parent directories recursively
- Idempotent (safe to call multiple times)
- No error if directory already exists

### Example
```python
ensure_dir('/path/to/cache')
# Creates /path/to/cache and any missing parents
```

---

## get_cache_dir()

### Purpose
Get platform-specific cache directory.

### Platform Behavior

**Windows:**
```
%LOCALAPPDATA%\weather-harvester\cache
Example: C:\Users\John\AppData\Local\weather-harvester\cache
```

**Linux/macOS:**
```
$XDG_CACHE_HOME/weather-harvester
or ~/.cache/weather-harvester
```

### Why Platform-Specific?
- Follows OS conventions
- Respects user preferences
- Integrates with system cleanup tools

### Example
```python
cache_dir = get_cache_dir()
# Returns appropriate path for current OS
```

---

## get_log_dir()

### Purpose
Get platform-specific log directory.

### Platform Behavior

**Windows:**
```
%LOCALAPPDATA%\weather-harvester\logs
```

**Linux/macOS:**
```
~/.local/share/weather-harvester/logs
```

### Example
```python
log_dir = get_log_dir()
# Returns appropriate path for current OS
```

---

## Design Patterns Used

### 1. Atomic Operations
- **Pattern**: Write to temp file, then rename
- **Benefit**: Prevents partial reads
- **Used in**: `atomic_write()`

### 2. Safe Defaults
- **Pattern**: Return default value on error
- **Benefit**: Graceful degradation
- **Used in**: `safe_read_json()`

### 3. Platform Abstraction
- **Pattern**: OS-specific logic hidden behind common interface
- **Benefit**: Cross-platform compatibility
- **Used in**: `get_cache_dir()`, `get_log_dir()`

### 4. Input Sanitization
- **Pattern**: Clean untrusted input before use
- **Benefit**: Security and stability
- **Used in**: `sanitize_string()`

---

## Error Handling Strategy

### File Operations
```python
try:
    # Attempt operation
    with open(filepath, 'w') as f:
        f.write(content)
except Exception:
    # Clean up temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
    raise  # Re-raise for caller to handle
```

### JSON Operations
```python
try:
    return json.load(f)
except (json.JSONDecodeError, IOError):
    return default  # Graceful fallback
```

---

## Testing Considerations

### Testable Functions
- All functions are pure or have clear side effects
- Platform-specific code can be mocked
- File operations use temp directories in tests

### Test Coverage
- Atomic write success/failure
- JSON read/write with invalid data
- Platform detection
- String sanitization edge cases

---

## Performance Characteristics

| Function | Time Complexity | Notes |
|----------|----------------|-------|
| `atomic_write()` | O(n) | n = content size |
| `safe_read_json()` | O(n) | n = file size |
| `safe_write_json()` | O(n) | n = data size |
| `get_timestamp()` | O(1) | Constant time |
| `sanitize_string()` | O(n) | n = string length |
| `ensure_dir()` | O(d) | d = directory depth |
| `get_cache_dir()` | O(1) | Cached after first call |

---

## Dependencies

### Standard Library Imports
```python
import os           # File system operations
import json         # JSON serialization
import tempfile     # Temporary file creation
import shutil       # File operations (move)
from datetime import datetime  # Timestamps
```

### No External Dependencies
All functionality uses Python standard library only.

---

## Common Usage Patterns

### Cache File Management
```python
# Read cache
data = safe_read_json(cache_path, default={})

# Update cache
data['new_key'] = 'new_value'

# Write cache atomically
safe_write_json(cache_path, data)
```

### Directory Setup
```python
# Ensure directories exist
cache_dir = get_cache_dir()
log_dir = get_log_dir()

# Both directories now guaranteed to exist
```

### Safe Logging
```python
# Sanitize user input before logging
user_input = request.get('location')
safe_input = sanitize_string(user_input)
logger.info(f"Fetching weather for: {safe_input}")
```

---

## Best Practices

1. **Always use atomic_write() for important data**
   - Prevents corruption on crashes
   - Safe for concurrent access

2. **Use safe_read_json() with defaults**
   - Graceful handling of missing files
   - No need for existence checks

3. **Sanitize external input**
   - Before logging
   - Before storing
   - Before displaying

4. **Use platform-specific directories**
   - Respects OS conventions
   - Avoids permission issues

---

## Future Enhancements

Potential improvements:
- File locking for concurrent access
- Compression for large cache files
- Configurable cache/log locations
- Async file I/O support
- Backup/restore utilities
