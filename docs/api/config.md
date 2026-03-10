# sniff.config

Configuration management -- TOML-based layered configuration with env var override.

**Module:** `sniff.config`
**Tier:** 1 (Core Detection)
**Side effects:** `save()` writes to disk

---

## Classes

### ConfigManager

```
class ConfigManager
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_name` | `str` | -- | Application name (used for file naming) |
| `defaults` | `dict` | `{}` | Default configuration values |

**Precedence (highest to lowest):** environment variables > project config > user config > system config > defaults.

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get(key)` | `Any` | Get a config value by dotted key path |
| `set(key, value)` | `None` | Set a config value |
| `save()` | `None` | Write current config to project config file |

---

## Examples

```python
from sniff import ConfigManager

config = ConfigManager("myapp", defaults={"database": {"path": "/tmp/db"}})
db_path = config.get("database.path")
config.set("api.timeout", 30)
config.save()
```
