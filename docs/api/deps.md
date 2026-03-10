# sniff.deps

Dependency checking -- verify CLI tool availability and version constraints.

**Module:** `sniff.deps`
**Tier:** 1 (Core Detection)
**Side effects:** Runs subprocesses to detect tool versions

---

## Classes

### DependencySpec

```
@dataclass(frozen=True)
class DependencySpec
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Human-readable name (e.g., `"CMake"`) |
| `command` | `str` | -- | Binary to check (e.g., `"cmake"`) |
| `min_version` | `str \| None` | `None` | Minimum version requirement |
| `version_arg` | `str` | `"--version"` | Argument to get version string |
| `version_pattern` | `str \| None` | `None` | Regex pattern to extract version |
| `required` | `bool` | `True` | Whether this dependency is required |

### DependencyResult

```
@dataclass(frozen=True)
class DependencyResult
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | `str` | -- | Command that was checked |
| `found` | `bool` | `False` | Whether the binary was found |
| `version` | `str \| None` | `None` | Detected version string |
| `path` | `str \| None` | `None` | Resolved binary path |
| `ok` | `bool` | `False` | Found and meets minimum version |
| `meets_minimum` | `bool` | `True` | Version meets minimum (True if no minimum set) |

### DependencyChecker

```
class DependencyChecker
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `float` | `10.0` | Timeout for version subprocess calls |

#### check

```python
def check(self, spec: DependencySpec) -> DependencyResult
```

Check a single dependency. Always succeeds.

---

## Examples

```python
from sniff import DependencyChecker, DependencySpec

checker = DependencyChecker()
result = checker.check(DependencySpec("Rust", "rustc", min_version="1.80"))

if result.ok:
    print(f"Rust {result.version} at {result.path}")
else:
    print(f"Rust not found or below 1.80")
```
