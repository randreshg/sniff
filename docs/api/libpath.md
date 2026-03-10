# sniff.libpath

Platform-aware library path resolution and management.

**Module:** `sniff.libpath`
**Tier:** 2 (Extended Detection)
**Side effects:** `apply()` modifies `os.environ` (the only side-effecting method in sniff)

---

## Classes

### LibraryPathInfo

```
@dataclass(frozen=True)
class LibraryPathInfo
```

Resolved library path state.

| Field | Type | Description |
|-------|------|-------------|
| `env_var` | `str` | Environment variable name (`LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`, or `PATH`) |
| `paths` | `tuple[str, ...]` | Ordered list of directories |
| `platform` | `PlatformInfo` | Platform info used for resolution |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `as_string` | `str` | Paths joined with platform separator (`:` on Unix, `;` on Windows) |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `contains(path)` | `bool` | Check if a directory is in the library path (normalized comparison) |

---

### LibraryPathResolver

```
class LibraryPathResolver
```

Platform-aware library path resolution and manipulation. Builds library path values
without modifying the environment until `apply()` is called.

**Platform mapping:**

| OS | Environment Variable |
|----|---------------------|
| Linux | `LD_LIBRARY_PATH` |
| macOS | `DYLD_LIBRARY_PATH` |
| Windows | `PATH` |

#### Construction

```python
# Auto-detect platform
resolver = LibraryPathResolver()

# From current platform (explicit)
resolver = LibraryPathResolver.for_current_platform()

# For a specific platform
resolver = LibraryPathResolver.for_platform("Linux", "x86_64")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `platform_info` | `PlatformInfo \| None` | `None` | Platform info. Auto-detected if `None`. |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `env_var` | `str` | The environment variable name for this platform |
| `platform_info` | `PlatformInfo` | The platform info used by this resolver |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `prepend(*paths)` | `self` | Add directories to the front. Duplicates skipped. |
| `append(*paths)` | `self` | Add directories to the end. Duplicates skipped. |
| `resolve()` | `LibraryPathInfo` | Compute final path (prepends + current env + appends). Does not modify env. |
| `apply()` | `LibraryPathInfo` | Resolve and write to `os.environ`. |
| `to_env_var()` | `tuple[str, str]` | Return `(env_var_name, value)` tuple for use with `ActivationScriptBuilder`. |

---

## Examples

### Prepend library paths

```python
from sniff.libpath import LibraryPathResolver

resolver = LibraryPathResolver.for_current_platform()
resolver.prepend("/opt/conda/lib")
resolver.prepend("/opt/llvm/lib")

info = resolver.resolve()
print(f"{info.env_var} = {info.as_string}")
# LD_LIBRARY_PATH = /opt/llvm/lib:/opt/conda/lib:...existing...
```

### Apply to environment

```python
from sniff.libpath import LibraryPathResolver

resolver = LibraryPathResolver()
resolver.prepend("/opt/mlir/lib").append("/usr/local/lib")
info = resolver.apply()  # Writes to os.environ
```

### Use with shell activation scripts

```python
from sniff.libpath import LibraryPathResolver
from sniff.shell import EnvVar

resolver = LibraryPathResolver()
resolver.prepend("/opt/conda/lib")
name, value = resolver.to_env_var()
env = EnvVar(name=name, value=value, prepend_path=True)
```

### Cross-platform usage

```python
from sniff.libpath import LibraryPathResolver

# Generate paths for macOS even when running on Linux
resolver = LibraryPathResolver.for_platform("Darwin", "arm64")
resolver.prepend("/opt/homebrew/lib")
info = resolver.resolve()
print(info.env_var)  # "DYLD_LIBRARY_PATH"
```
