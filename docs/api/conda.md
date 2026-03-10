# sniff.conda

Conda environment detection -- find active and available conda environments.

**Module:** `sniff.conda`
**Tier:** 1 (Core Detection)
**Side effects:** May run subprocess to list conda environments

---

## Classes

### CondaEnvironment

```
@dataclass(frozen=True)
class CondaEnvironment
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Environment name |
| `prefix` | `Path` | -- | Environment prefix path |
| `python_version` | `str \| None` | `None` | Python version in this environment |
| `is_active` | `bool` | `False` | Whether this env is currently active |

### CondaDetector

```
class CondaDetector
```

#### find_active

```python
def find_active(self) -> CondaEnvironment | None
```

Find the currently active conda environment. Returns `None` if no conda env is active.

---

## Examples

```python
from sniff import CondaDetector

conda = CondaDetector()
env = conda.find_active()
if env:
    print(f"Active: {env.name} at {env.prefix}")
    print(f"Python: {env.python_version}")
```
