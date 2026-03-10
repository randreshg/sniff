# sniff.diagnostic

Diagnostic framework -- extensible health checks with pluggable formatters.

**Module:** `sniff.diagnostic`
**Tier:** 3 (Frameworks)
**Side effects:** None (checks may run subprocesses via consumer implementations)

Provides a protocol-based diagnostic system where consumers register checks and
sniff runs them, collects results, and formats reports.

---

## Classes

### CheckStatus

```
enum CheckStatus(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `PASS` | Check passed |
| `WARN` | Check produced a warning |
| `FAIL` | Check failed |
| `SKIP` | Check was skipped |

---

### CheckResult

```
@dataclass(frozen=True)
class CheckResult
```

Result of running one diagnostic check.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Check identifier |
| `status` | `CheckStatus` | -- | Outcome |
| `summary` | `str` | `""` | One-line summary |
| `details` | `dict[str, str]` | `{}` | Structured metadata |
| `fix_hint` | `str \| None` | `None` | Suggested fix |
| `elapsed_ms` | `float` | `0.0` | Execution time in milliseconds |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `ok` | `bool` | `True` unless the check failed |

---

### DiagnosticReport

```
@dataclass(frozen=True)
class DiagnosticReport
```

Aggregated results from a diagnostic run.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `results` | `tuple[CheckResult, ...]` | -- | All check results |
| `elapsed_ms` | `float` | `0.0` | Total execution time |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `passed` | `int` | Number of passed checks |
| `warned` | `int` | Number of warned checks |
| `failed` | `int` | Number of failed checks |
| `skipped` | `int` | Number of skipped checks |
| `ok` | `bool` | `True` if no checks failed |

---

## Protocols

### DiagnosticCheck

```
@runtime_checkable
class DiagnosticCheck(Protocol)
```

Protocol for a single diagnostic check. Consumers implement this to add custom
health checks.

| Property/Method | Type | Description |
|----------------|------|-------------|
| `name` (property) | `str` | Short machine-friendly identifier (e.g., `"python-version"`) |
| `category` (property) | `str` | Grouping key (e.g., `"platform"`, `"deps"`, `"ci"`) |
| `description` (property) | `str` | One-line human description |
| `run()` | `CheckResult` | Execute the check. Must never raise. |

---

## Classes (continued)

### CheckRegistry

```
class CheckRegistry
```

Central registry for diagnostic checks.

| Method | Returns | Description |
|--------|---------|-------------|
| `register(check)` | `None` | Register a check. Raises `TypeError` if protocol not satisfied. |
| `checks()` | `list[DiagnosticCheck]` | All registered checks in insertion order |
| `by_category(category)` | `list[DiagnosticCheck]` | Checks matching a category |
| `categories()` | `list[str]` | Unique categories in insertion order |

---

### DiagnosticRunner

```
class DiagnosticRunner
```

Run diagnostic checks and produce reports. Catches exceptions from check
implementations and converts them to `FAIL` results.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `registry` | `CheckRegistry \| None` | `None` | Shared registry. Creates one if `None`. |

| Method | Returns | Description |
|--------|---------|-------------|
| `register(check)` | `None` | Convenience: delegate to underlying registry |
| `run_all()` | `DiagnosticReport` | Run every registered check |
| `run_category(category)` | `DiagnosticReport` | Run checks in a single category |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `registry` | `CheckRegistry` | The underlying check registry |

---

### Formatters

#### TextFormatter

Render a `DiagnosticReport` as plain text.

```python
formatter = TextFormatter()
print(formatter.format(report))
```

Output:

```
  [PASS] platform: Linux x86_64
  [PASS] dep-cmake: CMake 3.28.0
  [FAIL] dep-ninja: ninja not found
         hint: Install ninja

  2 passed, 0 warned, 1 failed, 0 skipped (42ms)
```

#### JsonFormatter

Render as JSON with `results` array and `summary` object.

#### MarkdownFormatter

Render as a Markdown table with status, check name, and summary columns.

---

## Examples

### Implement a custom check

```python
from sniff.diagnostic import CheckResult, CheckStatus

class PythonVersionCheck:
    @property
    def name(self) -> str:
        return "python-version"

    @property
    def category(self) -> str:
        return "platform"

    @property
    def description(self) -> str:
        return "Python >= 3.11"

    def run(self) -> CheckResult:
        import sys
        if sys.version_info >= (3, 11):
            return CheckResult(
                name=self.name, status=CheckStatus.PASS,
                summary=f"Python {sys.version_info.major}.{sys.version_info.minor}",
            )
        return CheckResult(
            name=self.name, status=CheckStatus.FAIL,
            summary=f"Python {sys.version_info.major}.{sys.version_info.minor} (need 3.11+)",
            fix_hint="Install Python 3.11 or newer",
        )
```

### Build a doctor command

```python
from sniff.diagnostic import DiagnosticRunner, TextFormatter
from sniff.diagnostic_checks import PlatformCheck, DependencyCheck, CIEnvironmentCheck
from sniff.deps import DependencySpec

runner = DiagnosticRunner()
runner.register(PlatformCheck())
runner.register(DependencyCheck(DependencySpec("CMake", "cmake", min_version="3.20")))
runner.register(DependencyCheck(DependencySpec("Rust", "rustc", min_version="1.80")))
runner.register(CIEnvironmentCheck())

report = runner.run_all()
print(TextFormatter().format(report))

if not report.ok:
    exit(1)
```

### Run checks by category

```python
from sniff.diagnostic import DiagnosticRunner

runner = DiagnosticRunner()
# ... register checks ...

# Run only dependency checks
deps_report = runner.run_category("deps")
print(f"Dependencies: {deps_report.passed}/{len(deps_report.results)} passed")
```

### JSON output for CI

```python
from sniff.diagnostic import DiagnosticRunner, JsonFormatter

runner = DiagnosticRunner()
# ... register checks ...

report = runner.run_all()
print(JsonFormatter().format(report))
```
