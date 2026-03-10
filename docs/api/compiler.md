# sniff.compiler

Compiler and toolchain detection -- identify installed compilers, versions, and targets.

**Module:** `sniff.compiler`
**Tier:** 2 (Extended Detection)
**Side effects:** Runs subprocesses to detect compiler versions (with configurable timeout)

---

## Classes

### CompilerFamily

```
enum CompilerFamily(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `GCC` | GNU Compiler Collection |
| `CLANG` | LLVM/Clang |
| `RUSTC` | Rust compiler |
| `GO` | Go compiler |
| `UNKNOWN` | Unknown compiler family |

---

### CompilerInfo

```
@dataclass(frozen=True)
class CompilerInfo
```

Detection result for a single compiler.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `family` | `CompilerFamily` | -- | Compiler family |
| `command` | `str` | -- | Binary name used (e.g., `"gcc-13"`, `"clang"`) |
| `path` | `str \| None` | `None` | Resolved path from `shutil.which()` |
| `version` | `str \| None` | `None` | Version string (e.g., `"13.2.0"`) |
| `target` | `str \| None` | `None` | Default target triple (e.g., `"x86_64-linux-gnu"`) |
| `language` | `str \| None` | `None` | Primary language: `"c"`, `"c++"`, `"rust"`, `"go"` |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `found` | `bool` | `True` if the compiler was found in PATH |

---

### ToolchainInfo

```
@dataclass(frozen=True)
class ToolchainInfo
```

Aggregated toolchain detection results.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `compilers` | `tuple[CompilerInfo, ...]` | `()` | All probed compilers |
| `default_cc` | `CompilerInfo \| None` | `None` | Default C compiler (`cc` / `$CC`) |
| `default_cxx` | `CompilerInfo \| None` | `None` | Default C++ compiler (`c++` / `$CXX`) |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `families` | `tuple[CompilerFamily, ...]` | Unique compiler families detected |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `by_family(family)` | `tuple[CompilerInfo, ...]` | All compilers matching a given family |
| `by_language(language)` | `tuple[CompilerInfo, ...]` | All compilers for a given language |

---

### CompilerDetector

```
class CompilerDetector
```

Detect installed compilers and their capabilities. Always succeeds (never raises).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `float` | `10.0` | Seconds to wait for version commands |

**Probed compilers:** `gcc`, `g++`, `clang`, `clang++`, `rustc`, `go`

#### detect

```python
def detect(self) -> ToolchainInfo
```

Detect all known compilers. Returns `ToolchainInfo` with all probed compilers,
including those not found (with `found=False`).

#### detect_compiler

```python
def detect_compiler(self, command: str) -> CompilerInfo
```

Detect a specific compiler by command name. Falls back to generic detection
for unknown commands.

---

## Detection Details

### Version extraction patterns

| Compiler | Command | Version Pattern | Target Extraction |
|----------|---------|-----------------|-------------------|
| gcc/g++ | `--version` | `(\d+\.\d+\.\d+)` | `Target: <triple>` |
| clang/clang++ | `--version` | `version (\d+\.\d+\.\d+)` | `Target: <triple>` |
| rustc | `--version` | `rustc (\d+\.\d+\.\d+)` | `rustc -vV` -> `host: <triple>` |
| go | `version` | `go(\d+\.\d+(?:\.\d+)?)` | `go env GOOS GOARCH` |

### Default compiler detection

The detector identifies the default C and C++ compilers by:
1. Checking `cc` / `c++` symlinks via `shutil.which()`
2. Matching against detected compilers by path
3. Falling back to the first found C/C++ compiler

---

## Examples

### Detect all compilers

```python
from sniff.compiler import CompilerDetector

detector = CompilerDetector()
info = detector.detect()

for c in info.compilers:
    if c.found:
        print(f"{c.command}: {c.version} ({c.target})")

if info.default_cc:
    print(f"Default CC: {info.default_cc.command} {info.default_cc.version}")
```

### Check for specific compiler

```python
from sniff.compiler import CompilerDetector, CompilerFamily

detector = CompilerDetector(timeout=5.0)
info = detector.detect()

clang = info.by_family(CompilerFamily.CLANG)
if clang:
    print(f"Clang {clang[0].version} at {clang[0].path}")

rust = info.by_language("rust")
if rust:
    print(f"Rust {rust[0].version}")
```

### Detect a single compiler

```python
from sniff.compiler import CompilerDetector

detector = CompilerDetector()
rustc = detector.detect_compiler("rustc")
if rustc.found:
    print(f"rustc {rustc.version} targeting {rustc.target}")
```
