# sniff.tools

Tool binary checking -- verify tool availability on PATH.

**Module:** `sniff.tools`
**Tier:** 1 (Core Detection)
**Side effects:** None

---

## Classes

### ToolChecker

```
class ToolChecker
```

#### which

```python
def which(self, name: str) -> str | None
```

Find a tool binary on PATH. Returns the resolved path or `None`.

#### get_version

```python
def get_version(self, name: str, version_arg: str = "--version") -> str | None
```

Get a tool's version string by running it with the given argument.

---

## Examples

```python
from sniff import ToolChecker

checker = ToolChecker()
cmake_path = checker.which("cmake")
if cmake_path:
    version = checker.get_version("cmake")
    print(f"CMake {version} at {cmake_path}")
```
