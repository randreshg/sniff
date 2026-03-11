# Sniff Architecture

## Executive Summary

Sniff is a development environment intelligence platform: zero dependencies at core, detection-only, frozen
dataclasses, protocol-based extensions, always succeeds.

This document defines the module organization, public API surface, and extension points.

---

## 1. Core Principles (Inviolable)

These principles are load-bearing. Every design decision must satisfy all five:

1. **Zero dependencies** -- stdlib only. No tomli, no PyYAML, no requests. Conditional
   use of `tomllib` (3.11+) is acceptable with graceful degradation.

2. **Detection-only** -- sniff never modifies state. No file writes, no env var mutations,
   no package installs. Side effects exist only in consumer code via the Remediator protocol.

3. **Frozen dataclasses** -- all result types are `@dataclass(frozen=True)`. Immutability
   guarantees that detection results can be cached, shared across threads, and used as
   dict keys.

4. **Protocol-based extensions** -- sniff defines `Protocol` interfaces that consumers
   implement. sniff never imports consumer code.

5. **Always succeeds** -- every `detect()` method returns a valid result, never raises.
   Missing data produces `None` fields, not exceptions. Detection errors are swallowed
   internally and surfaced as optional diagnostic metadata.

---

## 2. Module Organization

### 2.1 Directory Structure

```
src/sniff/
├── __init__.py              # Public API re-exports (v1 compat + v2 additions)
├── _version.py              # __version__ = "2.0.0"
│
│   # ── Tier 1: Core Detection (stable, semver-protected) ──────────
├── detect.py                # PlatformDetector, PlatformInfo  [EXISTING]
├── deps.py                  # DependencyChecker, DependencySpec, DependencyResult  [EXISTING]
├── conda.py                 # CondaDetector, CondaEnvironment  [EXISTING]
├── ci.py                    # CIDetector, CIInfo, CIProvider, ...  [EXISTING]
├── workspace.py             # WorkspaceDetector, WorkspaceInfo, WorkspaceKind  [EXISTING]
├── tools.py                 # ToolChecker  [EXISTING]
├── config.py                # ConfigManager  [EXISTING]
│
│   # ── Tier 2: Extended Detection (stable after 2.1) ──────────────
├── paths.py                 # PathManager, PathInfo, ProjectPaths  [NEW]
├── build.py                 # BuildSystemDetector, BuildSystemInfo  [NEW]
├── versions.py              # VersionManager, VersionConstraint  [NEW]
├── shell.py                 # ShellDetector, ShellInfo, ShellCapabilities  [NEW]
├── env.py                   # EnvSetupDetector, EnvRequirements  [NEW]
│
│   # ── Tier 3: Frameworks (stable, protocol-only) ─────────────────
├── remediate.py             # Remediator, DetectedIssue, RemediatorRegistry  [EXISTING]
├── commands.py              # CommandRegistry protocol + base types  [NEW]
├── diagnostics.py           # DiagnosticFramework, Check, Report  [NEW]
├── templates.py             # ProjectTemplate protocol + scanner  [NEW]
│
│   # ── Internal (private, no stability guarantee) ─────────────────
├── _compat.py               # Python version compatibility shims
├── _toml.py                 # TOML loading (tomllib/tomli/fallback parser)
├── _subprocess.py           # Safe subprocess wrapper with timeout
└── _glob.py                 # Glob expansion utilities (extracted from workspace.py)
```

### 2.2 Tier Definitions

| Tier | Stability | Semver Protection | Import Path |
|------|-----------|-------------------|-------------|
| **Tier 1: Core** | Stable since 0.1.0 | Full (breaking = major bump) | `from sniff import X` |
| **Tier 2: Extended** | Provisional in 2.0, stable in 2.1 | After stabilization | `from sniff import X` or `from sniff.paths import X` |
| **Tier 3: Frameworks** | Protocol-stable, impl-flexible | Protocols are semver-protected; registries may evolve | `from sniff import X` or `from sniff.diagnostics import X` |
| **Internal** | Unstable | None (prefixed with `_`) | Not importable by consumers |

### 2.3 Import Hierarchy

Dependency flow is strictly top-down. No cycles.

```
__init__.py (re-exports only, no logic)
    ├── Tier 1 modules (depend only on _internal)
    ├── Tier 2 modules (depend on Tier 1 + _internal)
    └── Tier 3 modules (depend on Tier 1 + Tier 2 + _internal)

_internal modules (depend only on stdlib)
```

Within tiers, allowed cross-dependencies:

- `paths.py` may import from `detect.py` (needs PlatformInfo for OS-specific paths)
- `build.py` may import from `workspace.py` (build system correlates with workspace kind)
- `env.py` may import from `detect.py`, `conda.py`, `deps.py`
- `diagnostics.py` may import from `remediate.py` (extends DetectedIssue)
- No other cross-dependencies

---

## 3. Public API Surface

### 3.1 Tier 1: Core API (Backward Compatible with v0.1.0)

All existing exports remain at their current import paths. APXM code requires zero changes.

```python
# __init__.py re-exports (unchanged from v0.1.0)
from sniff.detect import PlatformDetector, PlatformInfo
from sniff.deps import DependencyChecker, DependencySpec, DependencyResult
from sniff.conda import CondaDetector, CondaEnvironment
from sniff.ci import CIDetector, CIInfo, CIProvider
from sniff.workspace import WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject
from sniff.tools import ToolChecker
from sniff.config import ConfigManager
from sniff.remediate import (
    DetectedIssue, IssueSeverity, FixResult, FixStatus,
    Remediator, RemediatorRegistry,
)
```

### 3.2 Tier 2: Extended API (New in v2.0)

#### 3.2.1 Path Management (`sniff.paths`)

```python
@dataclass(frozen=True)
class PathInfo:
    """Resolved paths for a detected project."""
    project_root: Path              # Workspace/project root
    config_dir: Path | None         # .sniff/ or .apxm/ config directory
    build_dir: Path | None          # target/, build/, dist/
    source_dirs: tuple[Path, ...]   # src/, lib/, crates/
    tool_paths: dict[str, Path]     # name -> resolved binary path

@dataclass(frozen=True)
class ProjectPaths:
    """OS-aware project path conventions."""
    data_dir: Path      # XDG_DATA_HOME / AppData / ~/Library
    config_dir: Path    # XDG_CONFIG_HOME / AppData / ~/Library/Preferences
    cache_dir: Path     # XDG_CACHE_HOME / AppData/Local / ~/Library/Caches
    state_dir: Path     # XDG_STATE_HOME / AppData/Local

class PathManager:
    """Detect and resolve project paths."""
    def detect(self, root: Path | None = None) -> PathInfo: ...
    def user_dirs(self, app_name: str) -> ProjectPaths: ...
    def find_project_root(self, start: Path | None = None,
                          markers: Sequence[str] | None = None) -> Path | None: ...
```

#### 3.2.2 Build System Detection (`sniff.build`)

```python
class BuildSystem(enum.Enum):
    CARGO = "cargo"
    CMAKE = "cmake"
    MESON = "meson"
    MAKE = "make"
    NINJA = "ninja"
    PIP = "pip"
    POETRY = "poetry"
    HATCH = "hatch"
    UV = "uv"
    NPM = "npm"
    GRADLE = "gradle"
    MAVEN = "maven"
    BAZEL = "bazel"

@dataclass(frozen=True)
class BuildSystemInfo:
    """Detected build system configuration."""
    system: BuildSystem
    config_file: Path
    version: str | None = None
    targets: tuple[str, ...] = ()       # Available build targets/profiles
    features: tuple[str, ...] = ()      # Detected features (e.g., "workspaces", "incremental")
    tool_path: Path | None = None       # Path to build tool binary

class BuildSystemDetector:
    """Detect build systems in a project."""
    def detect(self, root: Path | None = None) -> list[BuildSystemInfo]: ...
    def detect_primary(self, root: Path | None = None) -> BuildSystemInfo | None: ...
```

#### 3.2.3 Version Management (`sniff.versions`)

```python
@dataclass(frozen=True)
class VersionConstraint:
    """A version requirement with comparison semantics."""
    raw: str                    # Original string (e.g., ">=3.20,<4.0")
    minimum: str | None = None
    maximum: str | None = None
    exact: str | None = None

    def satisfied_by(self, version: str) -> bool: ...

class VersionManager:
    """Parse and compare version strings."""
    def parse(self, version: str) -> tuple[int, ...]: ...
    def compare(self, a: str, b: str) -> int: ...  # -1, 0, 1
    def satisfies(self, version: str, constraint: str) -> bool: ...
    def latest(self, versions: Sequence[str]) -> str | None: ...
```

#### 3.2.4 Shell Detection (`sniff.shell`)

```python
@dataclass(frozen=True)
class ShellInfo:
    """Detected shell environment."""
    name: str               # "bash", "zsh", "fish", "tcsh", "powershell"
    path: Path              # /bin/bash, /usr/bin/zsh
    version: str | None = None
    is_login: bool = False
    is_interactive: bool = False
    config_files: tuple[Path, ...] = ()  # .bashrc, .zshrc, etc.

@dataclass(frozen=True)
class ShellCapabilities:
    """What the shell supports."""
    has_completions: bool = False    # Tab completion support
    has_prompt_hooks: bool = False   # PROMPT_COMMAND / precmd
    has_autoenv: bool = False        # direnv, autoenv, etc.
    activation_syntax: str = "posix" # "posix", "fish", "csh", "powershell"

class ShellDetector:
    """Detect current shell and its capabilities."""
    def detect(self) -> ShellInfo: ...
    def capabilities(self, shell: ShellInfo | None = None) -> ShellCapabilities: ...
    def activation_script(self, shell: ShellInfo | None = None,
                          env_vars: dict[str, str] | None = None) -> str: ...
```

#### 3.2.5 Environment Setup Detection (`sniff.env`)

```python
@dataclass(frozen=True)
class EnvRequirements:
    """What an environment needs to be functional."""
    python_version: VersionConstraint | None = None
    env_vars: dict[str, str] = field(default_factory=dict)     # Required env vars
    paths: tuple[Path, ...] = ()                                # Required PATH entries
    packages: tuple[DependencySpec, ...] = ()                   # Required tools
    conda_env: str | None = None                                # Expected conda env name
    setup_commands: tuple[str, ...] = ()                        # Commands to reproduce

@dataclass(frozen=True)
class EnvStatus:
    """Current environment readiness."""
    ready: bool
    missing_vars: tuple[str, ...] = ()
    missing_paths: tuple[Path, ...] = ()
    missing_deps: tuple[DependencyResult, ...] = ()
    warnings: tuple[str, ...] = ()

class EnvSetupDetector:
    """Detect whether an environment meets requirements."""
    def check(self, requirements: EnvRequirements) -> EnvStatus: ...
    def diff(self, current: EnvStatus, target: EnvRequirements) -> EnvRequirements: ...
```

### 3.3 Tier 3: Framework API (New in v2.0)

#### 3.3.1 Command Registry (`sniff.commands`)

```python
@dataclass(frozen=True)
class CommandInfo:
    """A detected or registered command."""
    name: str                   # e.g., "build", "test", "doctor"
    binary: str                 # e.g., "cargo", "cmake"
    args: tuple[str, ...] = ()  # Default arguments
    env: dict[str, str] = field(default_factory=dict)
    description: str = ""
    category: str = ""          # e.g., "build", "test", "lint"
    source: str = ""            # Where this command was defined

@runtime_checkable
class CommandProvider(Protocol):
    """Protocol for command discovery. Consumers implement this."""
    @property
    def name(self) -> str: ...
    def commands(self) -> Sequence[CommandInfo]: ...

class CommandRegistry:
    """Registry for discovered and user-defined commands."""
    def register_provider(self, provider: CommandProvider) -> None: ...
    def register(self, command: CommandInfo) -> None: ...
    def get(self, name: str) -> CommandInfo | None: ...
    def list(self, category: str | None = None) -> list[CommandInfo]: ...
    def resolve(self, name: str) -> tuple[str, ...] | None: ...
```

#### 3.3.2 Diagnostic Framework (`sniff.diagnostics`)

```python
@dataclass(frozen=True)
class DiagnosticCheck:
    """A single diagnostic check definition."""
    name: str
    category: str               # "platform", "deps", "env", "build", "config"
    description: str = ""

@dataclass(frozen=True)
class DiagnosticResult:
    """Result of running a diagnostic check."""
    check: DiagnosticCheck
    passed: bool
    severity: IssueSeverity = IssueSeverity.INFO
    message: str = ""
    details: dict[str, str] = field(default_factory=dict)
    fix_hint: str | None = None
    elapsed_ms: float = 0.0

@dataclass(frozen=True)
class DiagnosticReport:
    """Complete diagnostic report."""
    results: tuple[DiagnosticResult, ...]
    passed: int = 0
    warned: int = 0
    failed: int = 0
    elapsed_ms: float = 0.0

    @property
    def ok(self) -> bool:
        return self.failed == 0

@runtime_checkable
class DiagnosticProvider(Protocol):
    """Protocol for diagnostic check providers. Consumers implement this."""
    @property
    def name(self) -> str: ...
    def checks(self) -> Sequence[DiagnosticCheck]: ...
    def run(self, check: DiagnosticCheck) -> DiagnosticResult: ...

class DiagnosticRunner:
    """Run diagnostic checks and produce reports."""
    def register(self, provider: DiagnosticProvider) -> None: ...
    def run_all(self) -> DiagnosticReport: ...
    def run_category(self, category: str) -> DiagnosticReport: ...
```

#### 3.3.3 Project Templates (`sniff.templates`)

```python
@dataclass(frozen=True)
class TemplateInfo:
    """A detected project template or scaffold."""
    name: str
    path: Path
    description: str = ""
    variables: tuple[str, ...] = ()  # Template variables (e.g., "project_name")
    tags: tuple[str, ...] = ()       # e.g., ("rust", "cli", "library")

@runtime_checkable
class TemplateProvider(Protocol):
    """Protocol for template discovery. Consumers implement this."""
    @property
    def name(self) -> str: ...
    def templates(self) -> Sequence[TemplateInfo]: ...

class TemplateScanner:
    """Scan for project templates."""
    def register(self, provider: TemplateProvider) -> None: ...
    def scan(self, root: Path | None = None) -> list[TemplateInfo]: ...
    def find(self, name: str) -> TemplateInfo | None: ...
```

---

## 4. Backward Compatibility Strategy

### 4.1 Zero-Break Guarantee for v2.0

APXM's current imports must work without any code changes:

```python
# All of these MUST continue to work identically:
from sniff import PlatformDetector, PlatformInfo
from sniff import DependencyChecker, DependencySpec, DependencyResult
from sniff import CondaDetector, CondaEnvironment
from sniff import CIDetector, CIInfo, CIProvider
from sniff import WorkspaceDetector, WorkspaceInfo, WorkspaceKind
from sniff.ci import CIDetector, CIInfo, CIRunnerInfo  # submodule import
```

### 4.2 API Evolution Rules

1. **Adding fields to frozen dataclasses**: Always use `default` values. Existing code
   that doesn't pass the new field continues to work.

2. **Adding methods to detectors**: Free to add. Existing code doesn't call them.

3. **Changing return types**: Never. If a method returns `PlatformInfo`, it always will.

4. **Removing fields**: Never in a minor version. Deprecate with `@property` that warns,
   remove in next major.

5. **New modules**: Always additive. Never reorganize existing modules.

### 4.3 Deprecation Protocol

```python
import warnings

class PlatformInfo:
    @property
    def old_field(self) -> str:
        warnings.warn(
            "PlatformInfo.old_field is deprecated, use new_field instead. "
            "Will be removed in sniff 3.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.new_field
```

### 4.4 Version Compatibility Matrix

| sniff version | Python | APXM compat | Notes |
|---------------|--------|-------------|-------|
| 0.1.x | 3.10+ | Current | Baseline |
| 2.0.x | 3.10+ | Current + new features | Zero-break upgrade |
| 2.1.x | 3.10+ | Current + stabilized Tier 2 | Tier 2 APIs become semver-protected |
| 3.0.x | 3.11+ | Migration guide provided | Drop 3.10, remove deprecations |

---

## 5. Extension Points

### 5.1 Extension Architecture

Sniff uses the **provider pattern**: sniff defines Protocol interfaces, consumers register
implementations. Sniff never imports consumer code.

```
┌─────────────────────────────────────────────────────┐
│                    Consumer (APXM)                   │
│                                                      │
│  ApxmDiagnosticProvider   ApxmCommandProvider        │
│  ApxmRemediator           ApxmTemplateProvider       │
│         │                        │                   │
│         ▼                        ▼                   │
│  ┌─────────────────────────────────────────────┐    │
│  │          sniff Protocol Interfaces           │    │
│  │  DiagnosticProvider  CommandProvider          │    │
│  │  Remediator          TemplateProvider         │    │
│  └─────────────────────────────────────────────┘    │
│         │                        │                   │
│         ▼                        ▼                   │
│  ┌─────────────────────────────────────────────┐    │
│  │          sniff Registries                    │    │
│  │  DiagnosticRunner    CommandRegistry          │    │
│  │  RemediatorRegistry  TemplateScanner          │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 5.2 Extension Points Summary

| Extension Point | Protocol | Registry | Use Case |
|----------------|----------|----------|----------|
| Remediation | `Remediator` | `RemediatorRegistry` | Fix detected issues |
| Commands | `CommandProvider` | `CommandRegistry` | Discover/register build commands |
| Diagnostics | `DiagnosticProvider` | `DiagnosticRunner` | Custom health checks |
| Templates | `TemplateProvider` | `TemplateScanner` | Project scaffolding |

### 5.3 Consumer Extension Example (APXM)

```python
# In APXM's tools/scripts/diagnostics.py
from sniff import DiagnosticProvider, DiagnosticCheck, DiagnosticResult, IssueSeverity

class ApxmDiagnosticProvider:
    """APXM-specific diagnostic checks."""

    @property
    def name(self) -> str:
        return "apxm"

    def checks(self) -> list[DiagnosticCheck]:
        return [
            DiagnosticCheck("mlir-present", "build", "MLIR libraries installed"),
            DiagnosticCheck("conda-active", "env", "Correct conda env activated"),
            DiagnosticCheck("rust-nightly", "deps", "Rust nightly toolchain"),
        ]

    def run(self, check: DiagnosticCheck) -> DiagnosticResult:
        if check.name == "mlir-present":
            return self._check_mlir(check)
        # ... etc
```

---

## 6. Performance Design

### 6.1 Performance Budget

| Operation | Target | Strategy |
|-----------|--------|----------|
| `PlatformDetector().detect()` | < 5ms | Filesystem reads only, no subprocess |
| `CIDetector().detect()` | < 1ms | Environment variables only |
| `WorkspaceDetector().detect()` | < 50ms | File existence + TOML parse |
| `BuildSystemDetector().detect()` | < 50ms | File existence + config parse |
| `DependencyChecker.check(spec)` | < 10s | subprocess with timeout (configurable) |
| `ShellDetector().detect()` | < 5ms | Environment variables + file checks |
| `PathManager().detect()` | < 10ms | Filesystem walks (bounded depth) |
| Full diagnostic scan | < 30s | Parallelism via threading for subprocess calls |

### 6.2 Performance Strategies

1. **Lazy detection**: Tier 2 modules only do work when explicitly called. Importing
   `sniff` does not trigger any detection.

2. **Caching**: Detector instances may cache results. Since results are frozen, caching
   is safe. Use `functools.lru_cache` on methods that do filesystem/subprocess I/O.

3. **Bounded I/O**: Filesystem walks are depth-bounded (default: 3 levels). Glob
   expansion uses `Path.glob()` which is lazy.

4. **Subprocess timeout**: All subprocess calls use configurable timeouts (default: 10s).
   Timeout = return None, not raise.

5. **No import-time I/O**: Module-level code in sniff must not do I/O. Detectors are
   instantiated explicitly by the consumer.

### 6.3 Anti-Patterns to Avoid

- Never scan the entire filesystem. Always require a root or use bounded walks.
- Never make network calls. sniff is offline-only.
- Never block on user input. sniff is non-interactive.
- Never spawn background processes. Detection is synchronous and bounded.

---

## 7. Internal Refactoring

### 7.1 Shared Utilities Extraction

Several patterns are duplicated across existing modules. Extract them into `_internal`:

**`_toml.py`** -- Currently duplicated in `workspace.py` and `config.py`:
```python
def load_toml(path: Path) -> dict | None:
    """Load TOML file, returning None on any error."""
    ...
```

**`_subprocess.py`** -- Currently duplicated in `deps.py`, `conda.py`, `tools.py`:
```python
def run_safe(cmd: list[str], *, timeout: float = 10.0) -> tuple[str, str] | None:
    """Run subprocess, return (stdout, stderr) or None on any error."""
    ...
```

**`_glob.py`** -- Currently in `workspace.py`:
```python
def expand_globs(root: Path, patterns: list[str],
                 exclude: list[str] | None = None) -> list[Path]:
    """Expand glob patterns relative to root."""
    ...
```

### 7.2 Refactoring Rules

- Internal modules are prefixed with `_` and have no stability guarantee.
- Existing public modules import from internal modules but their public API is unchanged.
- Refactoring is done in a single commit that is behavior-preserving (verified by tests).

---

## 8. `__init__.py` Design

The top-level `__init__.py` serves as the stable public API surface. It re-exports
from all tiers but uses lazy imports for Tier 2/3 to avoid import-time overhead.

```python
"""sniff -- Development environment intelligence."""

# Tier 1: Core (always available, backward compatible)
from sniff.detect import PlatformDetector, PlatformInfo
from sniff.deps import DependencyChecker, DependencySpec, DependencyResult
from sniff.conda import CondaDetector, CondaEnvironment
from sniff.ci import CIDetector, CIInfo, CIProvider
from sniff.workspace import WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject
from sniff.tools import ToolChecker
from sniff.config import ConfigManager

# Tier 1: Remediation framework (existing)
from sniff.remediate import (
    DetectedIssue, IssueSeverity, FixResult, FixStatus,
    Remediator, RemediatorRegistry,
)

# Tier 2: Extended detection (new in 2.0)
from sniff.paths import PathManager, PathInfo, ProjectPaths
from sniff.build import BuildSystemDetector, BuildSystemInfo, BuildSystem
from sniff.versions import VersionManager, VersionConstraint
from sniff.shell import ShellDetector, ShellInfo, ShellCapabilities
from sniff.env import EnvSetupDetector, EnvRequirements, EnvStatus

# Tier 3: Frameworks (new in 2.0)
from sniff.commands import CommandRegistry, CommandInfo, CommandProvider
from sniff.diagnostics import (
    DiagnosticRunner, DiagnosticCheck, DiagnosticResult,
    DiagnosticReport, DiagnosticProvider,
)
from sniff.templates import TemplateScanner, TemplateInfo, TemplateProvider

from sniff._version import __version__

__all__ = [
    # Tier 1 (v0.1.0 compat)
    "PlatformDetector", "PlatformInfo",
    "DependencyChecker", "DependencySpec", "DependencyResult",
    "CondaDetector", "CondaEnvironment",
    "CIDetector", "CIInfo", "CIProvider",
    "WorkspaceDetector", "WorkspaceInfo", "WorkspaceKind", "SubProject",
    "ToolChecker",
    "ConfigManager",
    "DetectedIssue", "IssueSeverity", "FixResult", "FixStatus",
    "Remediator", "RemediatorRegistry",
    # Tier 2 (v2.0)
    "PathManager", "PathInfo", "ProjectPaths",
    "BuildSystemDetector", "BuildSystemInfo", "BuildSystem",
    "VersionManager", "VersionConstraint",
    "ShellDetector", "ShellInfo", "ShellCapabilities",
    "EnvSetupDetector", "EnvRequirements", "EnvStatus",
    # Tier 3 (v2.0)
    "CommandRegistry", "CommandInfo", "CommandProvider",
    "DiagnosticRunner", "DiagnosticCheck", "DiagnosticResult",
    "DiagnosticReport", "DiagnosticProvider",
    "TemplateScanner", "TemplateInfo", "TemplateProvider",
    # Meta
    "__version__",
]
```

---

## 9. APXM Migration Guide

### 9.1 Phase 0: Drop-in Upgrade (Zero Changes)

**Effort: 0 lines changed. Just bump sniff version.**

All existing APXM imports work identically:

```python
# These all continue to work unchanged:
from sniff import PlatformDetector, PlatformInfo          # apxm_env.py, config.py
from sniff import CondaDetector, CondaEnvironment          # apxm_env.py
from sniff import DependencyChecker, DependencySpec        # deps.py
from sniff import CIDetector, CIInfo, CIProvider           # doctor.py
from sniff import WorkspaceDetector, WorkspaceInfo         # test_sniff_integration.py
from sniff.ci import CIDetector, CIInfo                    # ci_env.py
from sniff.ci import CIRunnerInfo                          # test_sniff_integration.py
```

### 9.2 Phase 1: Adopt Path Management

**Affected files:** `tools/apxm_env.py` (ApxmConfig.detect, get_conda_prefix)

Replace hand-rolled project root detection with PathManager:

```python
# BEFORE (apxm_env.py:200-216)
@classmethod
def detect(cls) -> "ApxmConfig":
    current = Path(__file__).parent.resolve()
    if current.name == "tools":
        apxm_dir = current.parent
    else:
        apxm_dir = current
        while apxm_dir.parent != apxm_dir:
            if (apxm_dir / "Cargo.toml").exists() and (apxm_dir / "tools").exists():
                break
            apxm_dir = apxm_dir.parent
    ...

# AFTER
from sniff import PathManager

@classmethod
def detect(cls) -> "ApxmConfig":
    pm = PathManager()
    apxm_dir = pm.find_project_root(
        start=Path(__file__).parent,
        markers=["Cargo.toml", "tools"],
    ) or Path(__file__).parent.parent
    ...
```

Replace OS-specific user directory logic with ProjectPaths:

```python
# BEFORE
@property
def config_dir(self) -> Path:
    return Path.home() / ".apxm"

# AFTER
from sniff import PathManager

@property
def config_dir(self) -> Path:
    return PathManager().user_dirs("apxm").config_dir
```

### 9.3 Phase 2: Adopt Build System Detection

**Affected files:** `tools/scripts/doctor.py` (build status section)

```python
# BEFORE (doctor.py:177-182)
if config.compiler_bin.exists():
    print_success(msg.MSG_COMPILER_BIN_OK.format(path=config.compiler_bin))
else:
    print_warning(msg.MSG_COMPILER_NOT_BUILT)

# AFTER
from sniff import BuildSystemDetector

builds = BuildSystemDetector().detect(config.apxm_dir)
cargo = next((b for b in builds if b.system == BuildSystem.CARGO), None)
if cargo:
    print_success(f"Cargo workspace detected: {cargo.config_file}")
    if config.compiler_bin.exists():
        print_success(msg.MSG_COMPILER_BIN_OK.format(path=config.compiler_bin))
    else:
        print_warning(msg.MSG_COMPILER_NOT_BUILT)
```

### 9.4 Phase 3: Adopt Diagnostic Framework

**Affected files:** `tools/scripts/doctor.py` (entire file restructured)

Replace the monolithic doctor command with a DiagnosticRunner:

```python
# BEFORE: 233 lines of imperative checks in doctor.py

# AFTER: Declarative diagnostic providers
from sniff import DiagnosticRunner

def register_commands(app: typer.Typer) -> None:
    runner = DiagnosticRunner()
    runner.register(ApxmPlatformDiagnostics())
    runner.register(ApxmDependencyDiagnostics())
    runner.register(ApxmCondaDiagnostics())
    runner.register(ApxmBuildDiagnostics())
    runner.register(ApxmCIDiagnostics())

    @app.command()
    def doctor():
        """Check environment status and dependencies."""
        report = runner.run_all()
        render_report(report)  # Custom rendering with apxm_styles
        if not report.ok:
            raise typer.Exit(1)
```

### 9.5 Phase 4: Adopt Shell Integration

**Affected files:** `tools/apxm_env.py` (setup_mlir_environment)

```python
# BEFORE (apxm_env.py:177)
if PlatformDetector().detect().is_macos:
    env["DYLD_LIBRARY_PATH"] = ":".join(paths)
else:
    env["LD_LIBRARY_PATH"] = ":".join(paths)

# AFTER
from sniff import ShellDetector

shell = ShellDetector()
caps = shell.capabilities()
# ShellInfo already knows the right library path variable
lib_var = "DYLD_LIBRARY_PATH" if PlatformDetector().detect().is_macos else "LD_LIBRARY_PATH"
# Or use activation_script for shell-appropriate setup
script = shell.activation_script(env_vars={lib_var: ":".join(paths)})
```

### 9.6 Phase 5: Adopt Command Registry

**Affected files:** New integration in APXM CLI

```python
from sniff import CommandRegistry, CommandInfo

registry = CommandRegistry()
registry.register(CommandInfo(
    name="build",
    binary="cargo",
    args=("build", "--release"),
    category="build",
    description="Build APXM compiler",
))
registry.register(CommandInfo(
    name="test",
    binary="cargo",
    args=("test",),
    category="test",
    description="Run APXM test suite",
))
```

### 9.7 Migration Summary

| Phase | APXM Effort | Risk | Value |
|-------|-------------|------|-------|
| 0 | 0 lines | None | Access to all new APIs |
| 1 | ~20 lines | Low | Eliminate hand-rolled path logic |
| 2 | ~10 lines | Low | Richer build system awareness |
| 3 | ~100 lines | Medium | Extensible, testable doctor command |
| 4 | ~15 lines | Low | Shell-aware environment setup |
| 5 | ~30 lines | Low | Discoverable command registry |

Phases are independent. APXM can adopt them in any order, at any pace.

---

## 10. Testing Strategy

### 10.1 Test Organization

```
tests/
├── test_detect.py          # [EXISTING] Platform detection
├── test_deps.py            # [EXISTING] Dependency checking
├── test_ci.py              # [EXISTING] CI detection
├── test_config.py          # [EXISTING] Configuration
├── test_workspace.py       # [EXISTING] Workspace detection
├── test_paths.py           # [NEW] Path management
├── test_build.py           # [NEW] Build system detection
├── test_versions.py        # [NEW] Version management
├── test_shell.py           # [NEW] Shell detection
├── test_env.py             # [NEW] Environment setup
├── test_commands.py        # [NEW] Command registry
├── test_diagnostics.py     # [NEW] Diagnostic framework
├── test_templates.py       # [NEW] Template scanning
└── test_compat.py          # [NEW] v0.1.0 backward compatibility
```

### 10.2 Backward Compatibility Test

```python
# test_compat.py -- Ensures v0.1.0 API surface is preserved
def test_v1_imports():
    """All v0.1.0 imports must work."""
    from sniff import (
        CIDetector, CIInfo, CIProvider,
        CondaDetector, CondaEnvironment,
        DependencyChecker, DependencyResult, DependencySpec,
        PlatformDetector, PlatformInfo,
        WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject,
        ToolChecker, ConfigManager,
    )

def test_v1_submodule_imports():
    """v0.1.0 submodule imports must work."""
    from sniff.ci import CIDetector, CIInfo, CIRunnerInfo
    from sniff.detect import PlatformDetector, PlatformInfo
    from sniff.deps import DependencyChecker
    from sniff.conda import CondaDetector
    from sniff.workspace import WorkspaceDetector

def test_v1_behavior_unchanged():
    """Core detection behavior must be identical."""
    info = PlatformDetector().detect()
    assert isinstance(info, PlatformInfo)
    assert info.os in ("Linux", "Darwin", "Windows")
    # PlatformInfo must still be frozen
    with pytest.raises(AttributeError):
        info.os = "FreeBSD"
```

---

## 11. Documentation Structure

```
docs/
├── index.md                    # Overview + quick start
├── getting-started.md          # [EXISTING, updated] Installation + first steps
├── architecture.md             # This document (trimmed for public docs)
├── api/
│   ├── core.md                 # Tier 1 API reference
│   ├── extended.md             # Tier 2 API reference
│   ├── frameworks.md           # Tier 3 API reference
│   └── protocols.md            # Extension protocol reference
├── guides/
│   ├── migration-v2.md         # Migration from v0.1.x to v2.0
│   ├── extending.md            # How to write providers
│   ├── ci-integration.md       # CI/CD cookbook
│   └── performance.md          # Performance tuning guide
├── examples/
│   ├── doctor-command.md       # Building a doctor command
│   ├── env-setup.md            # Environment validation
│   └── build-detection.md      # Build system detection
└── changelog.md                # Version history
```

---

## 12. Release Plan

### v2.0.0-alpha.1
- Internal refactoring (_toml, _subprocess, _glob extraction)
- All Tier 1 modules unchanged
- `sniff.paths` and `sniff.versions` implemented
- Backward compatibility test suite

### v2.0.0-alpha.2
- `sniff.build` and `sniff.shell` implemented
- `sniff.env` implemented

### v2.0.0-beta.1
- `sniff.commands`, `sniff.diagnostics`, `sniff.templates` implemented
- Full test coverage
- Documentation draft

### v2.0.0-rc.1
- APXM integration tested (Phase 0 verified)
- Performance benchmarks pass
- API review complete

### v2.0.0
- Stable release
- Tier 1 APIs are semver-protected
- Tier 2 APIs are provisional (may change in 2.1)

### v2.1.0
- Tier 2 APIs stabilized and semver-protected
- Incorporate feedback from APXM Phase 1-2 adoption
