# sniff.diagnostic_checks

Built-in diagnostic checks for common environment concerns.

**Module:** `sniff.diagnostic_checks`
**Tier:** 3 (Frameworks)
**Side effects:** May run subprocesses (via `DependencyChecker`)

These checks use existing sniff detectors and expose them through the
`DiagnosticCheck` protocol so consumers can include them in a `DiagnosticRunner`
without writing boilerplate.

---

## Classes

### PlatformCheck

```
class PlatformCheck
```

Detect the current platform and report key details (OS, architecture,
distro, WSL/container status).

| Property | Value |
|----------|-------|
| `name` | `"platform"` |
| `category` | `"platform"` |

**Reported details:** `os`, `arch`, `distro`, `distro_version`, `pkg_manager`, `wsl`, `container`

**Always passes** (platform detection never fails).

---

### DependencyCheck

```
class DependencyCheck
```

Check that a CLI dependency is available and meets version requirements.
Wraps a `DependencySpec` and adapts the result to the diagnostic framework.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `spec` | `DependencySpec` | -- | Dependency specification to check |
| `timeout` | `float` | `10.0` | Timeout for subprocess version detection |

| Property | Value |
|----------|-------|
| `name` | `"dep-<command>"` |
| `category` | `"deps"` |

**Possible outcomes:**
- `PASS` -- dependency found, meets version requirement
- `WARN` -- found but below minimum version, or optional dependency missing
- `FAIL` -- required dependency not found

**Provides `fix_hint`** when dependency is missing or below minimum version.

---

### CIEnvironmentCheck

```
class CIEnvironmentCheck
```

Detect CI/CD environment and report provider details.

| Property | Value |
|----------|-------|
| `name` | `"ci-environment"` |
| `category` | `"ci"` |

**Possible outcomes:**
- `PASS` -- running in CI (reports provider, branch, commit)
- `SKIP` -- not running in CI

**Reported details:** `provider`, `branch`, `commit`, `runner_os`

---

## Examples

### Register built-in checks

```python
from sniff.diagnostic import DiagnosticRunner
from sniff.diagnostic_checks import PlatformCheck, DependencyCheck, CIEnvironmentCheck
from sniff.deps import DependencySpec

runner = DiagnosticRunner()

# Platform info
runner.register(PlatformCheck())

# Dependencies
runner.register(DependencyCheck(DependencySpec("Python", "python3", min_version="3.11")))
runner.register(DependencyCheck(DependencySpec("Git", "git")))
runner.register(DependencyCheck(
    DependencySpec("Docker", "docker", required=False),
    timeout=5.0,
))

# CI detection
runner.register(CIEnvironmentCheck())

report = runner.run_all()
```

### Combine with custom checks

```python
from sniff.diagnostic import DiagnosticRunner, CheckResult, CheckStatus
from sniff.diagnostic_checks import PlatformCheck, DependencyCheck
from sniff.deps import DependencySpec

class CondaEnvCheck:
    @property
    def name(self) -> str:
        return "conda-env"

    @property
    def category(self) -> str:
        return "environment"

    @property
    def description(self) -> str:
        return "Correct conda environment is active"

    def run(self) -> CheckResult:
        import os
        prefix = os.environ.get("CONDA_PREFIX", "")
        if "apxm" in prefix:
            return CheckResult(name=self.name, status=CheckStatus.PASS,
                             summary=f"Conda env: {prefix}")
        if prefix:
            return CheckResult(name=self.name, status=CheckStatus.WARN,
                             summary=f"Wrong conda env: {prefix}",
                             fix_hint="conda activate apxm")
        return CheckResult(name=self.name, status=CheckStatus.FAIL,
                         summary="No conda env active",
                         fix_hint="conda activate apxm")

runner = DiagnosticRunner()
runner.register(PlatformCheck())
runner.register(CondaEnvCheck())
runner.register(DependencyCheck(DependencySpec("CMake", "cmake", min_version="3.20")))
```
