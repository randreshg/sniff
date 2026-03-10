# sniff.env

Environment variable snapshot and composable builder.

**Module:** `sniff.env`
**Tier:** 2 (Extended Detection)
**Side effects:** None (`EnvSnapshot.capture()` reads `os.environ` but does not mutate it)

---

## Classes

### EnvSnapshot

```
@dataclass(frozen=True)
class EnvSnapshot
```

Immutable snapshot of environment variables. Safe to cache, share across threads,
and use as dict keys.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `vars` | `tuple[tuple[str, str], ...]` | `()` | Sorted key-value pairs |

#### Class Methods

**`capture() -> EnvSnapshot`** -- Capture the current `os.environ` as a frozen snapshot.

**`from_dict(d: Mapping[str, str]) -> EnvSnapshot`** -- Create from an arbitrary mapping.

#### Instance Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get(name, default=None)` | `str \| None` | Get a variable by name |
| `to_dict()` | `dict[str, str]` | Convert to a plain dict |
| `names()` | `tuple[str, ...]` | Return sorted variable names |
| `__contains__(name)` | `bool` | Check if a variable exists |
| `__len__()` | `int` | Number of variables |

---

### EnvVarBuilder

```
class EnvVarBuilder
```

Composable builder for constructing environment variable sets.
All mutating methods return `self` for chaining.

#### Setters

| Method | Description |
|--------|-------------|
| `set(name, value)` | Set a variable, overwriting any previous value |
| `set_default(name, value)` | Set only if not already set in this builder |
| `set_from_path(name, paths, sep=os.pathsep)` | Set by joining paths with separator |
| `unset(name)` | Mark a variable for removal |

#### Composition

| Method | Description |
|--------|-------------|
| `merge(other)` | Merge from another `EnvVarBuilder`, `EnvSnapshot`, or `Mapping`. Existing values take precedence. |

#### Terminal Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `build()` | `EnvSnapshot` | Produce a frozen snapshot |
| `to_dict()` | `dict[str, str]` | Return current state as dict |

---

## Examples

### Capture current environment

```python
from sniff.env import EnvSnapshot

snap = EnvSnapshot.capture()
print(f"HOME = {snap.get('HOME')}")
print(f"Variables: {len(snap)}")
```

### Build a custom environment

```python
from sniff.env import EnvVarBuilder

env = (
    EnvVarBuilder()
    .set("CC", "gcc")
    .set_default("JOBS", "4")
    .set_from_path("LD_LIBRARY_PATH", ["/opt/lib", "/usr/lib"])
    .build()
)

print(env.get("CC"))         # "gcc"
print(env.get("JOBS"))       # "4"
print(env.to_dict())         # full dict
```

### Merge environments

```python
from sniff.env import EnvVarBuilder, EnvSnapshot

base = EnvSnapshot.capture()
custom = (
    EnvVarBuilder()
    .set("MLIR_DIR", "/opt/llvm/lib/cmake/mlir")
    .unset("PYTHONDONTWRITEBYTECODE")
    .merge(base)
    .build()
)
```
