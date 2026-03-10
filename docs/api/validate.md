# sniff.validate

Environment validation -- run checks and produce reports.

**Module:** `sniff.validate`
**Tier:** 2 (Extended Detection)
**Side effects:** None (reads filesystem and env vars for checks)

Bridges detection results to the remediation system by producing `DetectedIssue`
instances for failed checks.

---

## Classes

### CheckStatus

```
enum CheckStatus(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `PASSED` | Check passed |
| `WARNING` | Check produced a warning |
| `FAILED` | Check failed |
| `SKIPPED` | Check was skipped |

---

### CheckResult

```
@dataclass(frozen=True)
class CheckResult
```

Result of a single validation check.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Check name |
| `status` | `CheckStatus` | -- | Outcome |
| `message` | `str` | `""` | Human-readable message |
| `category` | `str` | `"environment"` | Check category |
| `details` | `dict[str, str]` | `{}` | Structured metadata |
| `elapsed_ms` | `float` | `0.0` | Execution time in milliseconds |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `passed` | `bool` | `True` if the check passed |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_issue()` | `DetectedIssue \| None` | Convert to a `DetectedIssue` for remediation. Returns `None` for passed/skipped checks. |

---

### ValidationReport

```
@dataclass(frozen=True)
class ValidationReport
```

Aggregate report of all validation checks.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `results` | `tuple[CheckResult, ...]` | -- | All check results |
| `elapsed_ms` | `float` | `0.0` | Total execution time |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `passed` | `int` | Number of passed checks |
| `warnings` | `int` | Number of warning checks |
| `failed` | `int` | Number of failed checks |
| `skipped` | `int` | Number of skipped checks |
| `ok` | `bool` | `True` if no checks failed |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `issues()` | `list[DetectedIssue]` | Extract `DetectedIssue` instances from non-passing results |

---

### EnvironmentValidator

```
class EnvironmentValidator
```

Run environment validation checks and produce reports. Provides built-in checks
for common scenarios and accepts custom check functions. Never raises from check
execution.

#### Built-in Checks

| Method | Description |
|--------|-------------|
| `check_tool(command, *, name=None, category="dependency")` | Check that a CLI tool is available on PATH |
| `check_directory(path, *, name=None, category="environment")` | Check that a directory exists |
| `check_env_var(var, *, name=None, category="environment", expected=None)` | Check that an environment variable is set (optionally matches a value) |
| `check_file(path, *, name=None, category="config")` | Check that a file exists |

#### Registration and Execution

| Method | Description |
|--------|-------------|
| `add_check(check: CheckFn)` | Register a custom check function `() -> CheckResult` |
| `run_all()` | Run all registered checks, return `ValidationReport` |
| `run_checks(checks)` | Run an explicit list of check functions |

---

## Type Aliases

```python
CheckFn = Callable[[], CheckResult]
```

A check function: takes no arguments, returns a `CheckResult`.

---

## Examples

### Quick environment validation

```python
from sniff.validate import EnvironmentValidator

v = EnvironmentValidator()

# Run individual checks
result = v.check_tool("cmake", name="CMake")
print(f"{result.name}: {result.status.value} - {result.message}")

result = v.check_env_var("CONDA_PREFIX", name="Conda active")
result = v.check_directory("/opt/llvm/lib", name="LLVM libraries")
```

### Build and run a validation suite

```python
from sniff.validate import EnvironmentValidator, CheckResult, CheckStatus

v = EnvironmentValidator()

# Register built-in checks as lambdas
v.add_check(lambda: v.check_tool("cargo"))
v.add_check(lambda: v.check_tool("cmake"))
v.add_check(lambda: v.check_env_var("MLIR_DIR"))
v.add_check(lambda: v.check_directory("/opt/conda/envs/apxm"))

# Register a custom check
def check_rust_nightly():
    import subprocess
    try:
        result = subprocess.run(["rustc", "--version"], capture_output=True, text=True)
        if "nightly" in result.stdout:
            return CheckResult(name="rust-nightly", status=CheckStatus.PASSED,
                             message="Rust nightly toolchain active")
        return CheckResult(name="rust-nightly", status=CheckStatus.WARNING,
                         message="Rust stable (nightly recommended)")
    except FileNotFoundError:
        return CheckResult(name="rust-nightly", status=CheckStatus.FAILED,
                         message="rustc not found")

v.add_check(check_rust_nightly)

# Run all and get report
report = v.run_all()
print(f"Passed: {report.passed}, Failed: {report.failed}")
if not report.ok:
    for issue in report.issues():
        print(f"  [{issue.severity.value}] {issue.message}")
```

### Bridge to remediation

```python
from sniff.validate import EnvironmentValidator
from sniff.remediate import RemediatorRegistry

v = EnvironmentValidator()
v.add_check(lambda: v.check_tool("cmake"))
v.add_check(lambda: v.check_tool("ninja"))

report = v.run_all()
issues = report.issues()

registry = RemediatorRegistry()
# ... register remediators ...
for issue in issues:
    result = registry.fix(issue, dry_run=True)
```
