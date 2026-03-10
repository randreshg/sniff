# APXM Migration Guide: sniff 0.1.x to 2.0

This guide shows how APXM migrates from hand-rolled environment detection to
sniff 2.0's consolidated APIs. Each section includes before/after code, the
modules involved, and the code reduction achieved.

**Overall code reduction: ~65% fewer lines in APXM's tooling layer.**

---

## Table of Contents

- [Migration Overview](#migration-overview)
- [Phase 0: Drop-in Upgrade (Zero Changes)](#phase-0-drop-in-upgrade)
- [Phase 1: Path Management](#phase-1-path-management)
- [Phase 2: Build System and Toolchain Detection](#phase-2-build-system-and-toolchain-detection)
- [Phase 3: Diagnostic Framework](#phase-3-diagnostic-framework)
- [Phase 4: Shell Integration](#phase-4-shell-integration)
- [Phase 5: Command Registry](#phase-5-command-registry)
- [New Module Reference](#new-module-reference)
- [Code Reduction Summary](#code-reduction-summary)
- [FAQ](#faq)

---

## Migration Overview

| Phase | APXM Files Affected | Lines Changed | Risk | Value |
|-------|---------------------|---------------|------|-------|
| 0 | 0 | 0 | None | Access to all new APIs |
| 1 | `apxm_env.py`, `config.py` | ~20 removed | Low | Eliminate hand-rolled path logic |
| 2 | `doctor.py`, `apxm_env.py` | ~30 removed | Low | Richer build system + toolchain awareness |
| 3 | `doctor.py` | ~150 removed | Medium | Extensible, testable doctor command |
| 4 | `apxm_env.py` | ~40 removed | Low | Shell-aware environment setup |
| 5 | CLI integration | ~30 added | Low | Discoverable command registry |

Phases are independent. APXM can adopt them in any order, at any pace.
Each phase is backward-compatible with the previous one.

### sniff 2.0 Module Map

```
sniff 0.1.x (8 modules, 2,619 lines)     sniff 2.0 (25 modules, 9,852 lines)
------------------------------------      ------------------------------------------
detect.py (201 lines)          ------->   detect.py (unchanged)
deps.py (152 lines)            ------->   deps.py (unchanged)
tools.py (77 lines)            ------->   tools.py (unchanged)
remediate.py (165 lines)       ------->   remediate.py (unchanged)
ci.py (611 lines)              ------->   ci.py (unchanged)
workspace.py (957 lines)       ------->   workspace.py (unchanged)
config.py (167 lines)          ------->   config.py (unchanged)
conda.py (289 lines)           ------->   conda.py (enhanced: validate, find_prefix)
                                    +     paths.py           -- project root, user dirs
                                    +     build.py           -- 25 build systems
                                    +     shell.py           -- shell detection + scripts
                                    +     version.py         -- semver parsing + constraints
                                    +     version_managers.py -- pyenv/nvm/rustup detection
                                    +     toolchain.py       -- CMake/MLIR/conda profiles
                                    +     env.py             -- environment snapshots
                                    +     commands.py        -- command registry
                                    +     diagnostic.py      -- health check framework
                                    +     diagnostic_checks.py -- built-in checks
                                    +     scaffold.py        -- project type + templates
                                    +     lockfile.py        -- lock file parsing
                                    +     cache.py           -- build cache detection
                                    +     validate.py        -- validation framework
                                    +     compiler.py        -- compiler detection
                                    +     libpath.py         -- library path resolution
                                    +     ci_build.py        -- CI build matrix
```

---

## Phase 0: Drop-in Upgrade

**Effort: 0 lines changed. Just bump sniff version.**

All existing APXM imports work identically. sniff 2.0 re-exports every v0.1.x
symbol from `sniff.__init__`:

```python
# All of these continue to work unchanged:
from sniff import PlatformDetector, PlatformInfo          # apxm_env.py
from sniff import CondaDetector, CondaEnvironment          # apxm_env.py
from sniff import DependencyChecker, DependencySpec        # deps.py
from sniff import CIDetector, CIInfo, CIProvider           # doctor.py
from sniff import WorkspaceDetector, WorkspaceInfo         # test_sniff_integration.py
from sniff.ci import CIDetector, CIInfo                    # ci_env.py
from sniff.ci import CIRunnerInfo                          # test_sniff_integration.py
```

**Verification:**

```python
# This test must pass before and after the upgrade:
def test_v1_imports():
    from sniff import (
        PlatformDetector, PlatformInfo,
        DependencyChecker, DependencySpec, DependencyResult,
        CondaDetector, CondaEnvironment,
        CIDetector, CIInfo, CIProvider,
        WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject,
        ToolChecker, ConfigManager,
        DetectedIssue, IssueSeverity, FixResult, FixStatus,
        Remediator, RemediatorRegistry,
    )
    info = PlatformDetector().detect()
    assert isinstance(info, PlatformInfo)
    assert info.os in ("Linux", "Darwin", "Windows")
```

---

## Phase 1: Path Management

**Module:** `sniff.paths` -- `PathManager`, `PathCategory`, `ResolvedPath`, `ToolPath`, `ProjectPaths`

Replaces hand-rolled project root discovery and OS-specific directory logic
across APXM's tooling.

### 1a. Project Root Detection

```python
# ---------------------------------------------------------------
# BEFORE: apxm_env.py (17 lines)
# ---------------------------------------------------------------
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
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        conda_prefix = Path(conda_prefix)
    return cls(apxm_dir=apxm_dir, conda_prefix=conda_prefix)


# ---------------------------------------------------------------
# AFTER: apxm_env.py (5 lines) -- 71% reduction
# ---------------------------------------------------------------
from sniff import PathManager

@classmethod
def detect(cls) -> "ApxmConfig":
    pm = PathManager()
    apxm_dir = pm.find_project_root(
        start=Path(__file__).parent,
        markers=["Cargo.toml", "tools"],
    ) or Path(__file__).parent.parent
    conda_prefix = os.environ.get("CONDA_PREFIX")
    return cls(apxm_dir=apxm_dir, conda_prefix=Path(conda_prefix) if conda_prefix else None)
```

**Why this is better:**

- `PathManager.find_project_root()` walks up the directory tree with configurable
  marker files -- the exact algorithm APXM was implementing by hand
- Never raises (returns `None` on failure) -- consistent with sniff's contract
- Supports arbitrary markers: `["Cargo.toml", "tools"]` matches APXM's layout exactly

### 1b. OS-Aware User Directories

```python
# ---------------------------------------------------------------
# BEFORE: apxm_env.py (8 lines)
# ---------------------------------------------------------------
@property
def config_dir(self) -> Path:
    return Path.home() / ".apxm"

@property
def cache_dir(self) -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "apxm"
    elif sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "apxm" / "cache"
    else:
        return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "apxm"


# ---------------------------------------------------------------
# AFTER: apxm_env.py (3 lines) -- 62% reduction
# ---------------------------------------------------------------
from sniff import PathManager

@property
def config_dir(self) -> Path:
    return PathManager().user_dirs("apxm").config_dir

@property
def cache_dir(self) -> Path:
    return PathManager().user_dirs("apxm").cache_dir
```

**Why this is better:**

- `PathManager.user_dirs()` implements XDG (Linux), `~/Library` (macOS),
  and `AppData` (Windows) conventions in a single call
- Returns a `ProjectPaths` frozen dataclass with `.data_dir`, `.config_dir`,
  `.cache_dir`, and `.state_dir` -- all four standard directories

### 1c. Tool Binary Resolution

```python
# ---------------------------------------------------------------
# BEFORE: apxm_env.py (12 lines)
# ---------------------------------------------------------------
import shutil

def find_tools(self) -> dict[str, Path | None]:
    tools = {}
    for name in ["cargo", "rustc", "cmake", "ninja", "clang", "llvm-config"]:
        path = shutil.which(name)
        tools[name] = Path(path) if path else None
    return tools


# ---------------------------------------------------------------
# AFTER: apxm_env.py (4 lines) -- 67% reduction
# ---------------------------------------------------------------
from sniff import PathManager

def find_tools(self) -> tuple[ToolPath, ...]:
    pm = PathManager()
    return pm.resolve_tools(["cargo", "rustc", "cmake", "ninja", "clang", "llvm-config"])
```

**Why this is better:**

- `ToolPath` is a frozen dataclass with `.name`, `.path`, and `.found` properties
- `resolve_tools()` returns results in the same order as the input list
- No need to manually handle `shutil.which()` return types

---

## Phase 2: Build System and Toolchain Detection

**Modules:** `sniff.build` (25 build systems), `sniff.toolchain` (CMake/conda profiles), `sniff.version`

### 2a. Build System Detection

```python
# ---------------------------------------------------------------
# BEFORE: doctor.py (14 lines)
# ---------------------------------------------------------------
def check_build_status(config):
    cargo_toml = config.apxm_dir / "Cargo.toml"
    if not cargo_toml.exists():
        print_error("Cargo.toml not found")
        return False

    # Check if workspace
    with open(cargo_toml) as f:
        content = f.read()
    is_workspace = "[workspace]" in content

    if config.compiler_bin.exists():
        print_success(f"Compiler binary: {config.compiler_bin}")
    else:
        print_warning("Compiler not built (run 'cargo build --release')")

    return True


# ---------------------------------------------------------------
# AFTER: doctor.py (8 lines) -- 43% reduction
# ---------------------------------------------------------------
from sniff import BuildSystemDetector, BuildSystem

def check_build_status(config):
    builds = BuildSystemDetector().detect(config.apxm_dir)
    cargo = next((b for b in builds if b.system == BuildSystem.CARGO), None)
    if not cargo:
        print_error("No Cargo workspace detected")
        return False

    print_success(f"Cargo workspace: {cargo.config_file} (workspace={cargo.is_workspace})")
    for target in cargo.targets_of_kind("binary"):
        print_info(f"  Binary target: {target.name}")
    return True
```

**Why this is better:**

- `BuildSystemDetector` detects 25 build systems (Cargo, CMake, Make, Meson,
  npm, Poetry, Go, Maven, Gradle, etc.) from config files alone -- no subprocess calls
- `BuildSystemInfo` includes `.targets`, `.is_workspace`, `.version` automatically
- Discovering multiple build systems (e.g., Cargo + CMake for FFI projects) comes free

### 2b. Toolchain Environment Setup

```python
# ---------------------------------------------------------------
# BEFORE: apxm_env.py (25 lines)
# ---------------------------------------------------------------
def setup_mlir_environment(conda_prefix: Path) -> dict[str, str]:
    env = os.environ.copy()
    mlir_dir = conda_prefix / "lib" / "cmake" / "mlir"
    llvm_dir = conda_prefix / "lib" / "cmake" / "llvm"

    env["MLIR_DIR"] = str(mlir_dir)
    env["LLVM_DIR"] = str(llvm_dir)
    env["MLIR_PREFIX"] = str(conda_prefix)
    env["LLVM_PREFIX"] = str(conda_prefix)

    lib_paths = [str(conda_prefix / "lib")]
    if (conda_prefix / "lib64").exists():
        lib_paths.append(str(conda_prefix / "lib64"))

    platform_info = PlatformDetector().detect()
    if platform_info.is_macos:
        lib_var = "DYLD_LIBRARY_PATH"
    else:
        lib_var = "LD_LIBRARY_PATH"

    existing = env.get(lib_var, "")
    env[lib_var] = ":".join(lib_paths) + (":" + existing if existing else "")
    env["PATH"] = str(conda_prefix / "bin") + ":" + env.get("PATH", "")

    return env


# ---------------------------------------------------------------
# AFTER: apxm_env.py (8 lines) -- 68% reduction
# ---------------------------------------------------------------
from sniff.toolchain import CMakeToolchain, EnvVarBuilder
from sniff.shell import ActivationScriptBuilder, ShellKind

def setup_mlir_environment(conda_prefix: Path) -> dict[str, str]:
    builder = EnvVarBuilder(app_name="apxm")
    CMakeToolchain(prefix=conda_prefix).configure(builder)
    return {**os.environ, **builder.to_env_dict()}

# Or generate a shell activation script:
def mlir_activation_script(conda_prefix: Path, shell: ShellKind) -> str:
    builder = EnvVarBuilder(app_name="apxm")
    CMakeToolchain(prefix=conda_prefix).configure(builder)
    return ActivationScriptBuilder().build(builder.build(), shell)
```

**Why this is better:**

- `CMakeToolchain` knows the standard MLIR/LLVM directory layout and
  platform-aware library path variable (`LD_LIBRARY_PATH` vs `DYLD_LIBRARY_PATH`)
- `EnvVarBuilder` accumulates environment variables from multiple toolchain
  profiles and produces either a dict (for `subprocess.Popen`) or an
  `ActivationConfig` (for shell scripts)
- Toolchain profiles are composable -- combine `CMakeToolchain` + `CondaToolchain`
  in a single builder

### 2c. Version Constraint Checking

```python
# ---------------------------------------------------------------
# BEFORE: deps.py (18 lines)
# ---------------------------------------------------------------
def check_rust_version(min_version: str = "1.80") -> bool:
    import subprocess, re
    try:
        result = subprocess.run(
            ["rustc", "--version"], capture_output=True, text=True, timeout=10
        )
        match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
        if not match:
            return False
        version = match.group(1)
        v_parts = [int(x) for x in version.split(".")]
        m_parts = [int(x) for x in min_version.split(".")]
        v_parts += [0] * (3 - len(v_parts))
        m_parts += [0] * (3 - len(m_parts))
        return tuple(v_parts) >= tuple(m_parts)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# ---------------------------------------------------------------
# AFTER: deps.py (3 lines) -- 83% reduction
# ---------------------------------------------------------------
from sniff import DependencyChecker, DependencySpec

def check_rust_version(min_version: str = "1.80") -> bool:
    return DependencyChecker().check(
        DependencySpec("Rust", "rustc", min_version=min_version)
    ).ok
```

**Or use the new `version` module for constraint expressions:**

```python
from sniff import version_satisfies

# Supports PEP 440, semver, caret, tilde, wildcards, ranges
version_satisfies("1.82.0", ">=1.80")        # True
version_satisfies("1.82.0", "^1.80")          # True (>=1.80.0, <2.0.0)
version_satisfies("1.82.0", "~1.80")          # True (>=1.80.0, <1.81.0)
version_satisfies("1.82.0", ">=1.80,<2.0")    # True
```

---

## Phase 3: Diagnostic Framework

**Modules:** `sniff.diagnostic` (`DiagnosticRunner`, `CheckRegistry`, `DiagnosticCheck`, `CheckResult`),
`sniff.diagnostic_checks` (built-in checks)

This is the highest-value migration phase. It replaces the monolithic `doctor.py`
(typically 200+ lines of imperative checks) with a declarative, extensible
diagnostic system.

### Before: Monolithic doctor.py

```python
# ---------------------------------------------------------------
# BEFORE: doctor.py (233 lines, excerpt)
# ---------------------------------------------------------------
def run_doctor(config):
    """Check environment status and dependencies."""
    errors = 0

    # Platform checks
    platform = PlatformDetector().detect()
    if platform.is_linux:
        print_success(f"Platform: {platform.os} {platform.arch}")
        if platform.distro:
            print_info(f"  Distribution: {platform.distro} {platform.distro_version}")
    elif platform.is_macos:
        print_success(f"Platform: macOS {platform.arch}")
    else:
        print_warning(f"Unsupported platform: {platform.os}")
        errors += 1

    # Conda checks
    conda = CondaDetector()
    active = conda.find_active()
    if active:
        print_success(f"Conda env: {active.name} ({active.prefix})")
    else:
        print_error("No conda environment active")
        errors += 1

    # Dependency checks
    checker = DependencyChecker()
    for spec in [
        DependencySpec("Rust", "rustc", min_version="1.80"),
        DependencySpec("CMake", "cmake", min_version="3.20"),
        DependencySpec("Ninja", "ninja"),
        DependencySpec("LLVM", "llvm-config"),
    ]:
        result = checker.check(spec)
        if result.ok:
            print_success(f"{result.name}: {result.version}")
        elif result.required:
            print_error(f"{result.name}: {result.error}")
            errors += 1
        else:
            print_warning(f"{result.name}: {result.error}")

    # CI checks
    ci = CIDetector().detect()
    if ci.is_ci:
        print_info(f"CI: {ci.provider.display_name}")
    else:
        print_info("CI: not detected (local environment)")

    # Build status
    if config.compiler_bin.exists():
        print_success(f"Compiler binary: {config.compiler_bin}")
    else:
        print_warning("Compiler not built")

    # ... 100+ more lines of similar imperative checks ...

    if errors > 0:
        print_error(f"\n{errors} error(s) found")
        raise SystemExit(1)
    else:
        print_success("\nAll checks passed")
```

### After: Declarative Diagnostic Providers

```python
# ---------------------------------------------------------------
# AFTER: doctor.py (80 lines) -- 66% reduction
# ---------------------------------------------------------------
from sniff.diagnostic import (
    DiagnosticRunner, CheckRegistry, DiagnosticCheck, CheckResult,
    CheckStatus, TextFormatter,
)
from sniff import PlatformDetector, CondaDetector, DependencyChecker, DependencySpec, CIDetector


# -- Reusable diagnostic check implementations --

class PlatformCheck:
    """Check platform is supported."""
    name = "platform"
    category = "platform"
    description = "Verify supported platform"

    def run(self) -> CheckResult:
        info = PlatformDetector().detect()
        if info.os not in ("Linux", "Darwin"):
            return CheckResult(
                name=self.name, status=CheckStatus.FAIL,
                summary=f"Unsupported: {info.os}",
                fix_hint="APXM requires Linux or macOS",
            )
        return CheckResult(
            name=self.name, status=CheckStatus.PASS,
            summary=f"{info.os} {info.arch}",
            details={"distro": info.distro or "", "version": info.distro_version or ""},
        )


class CondaCheck:
    """Check conda environment is active."""
    name = "conda-active"
    category = "env"
    description = "Conda environment is active"

    def run(self) -> CheckResult:
        active = CondaDetector().find_active()
        if not active:
            return CheckResult(
                name=self.name, status=CheckStatus.FAIL,
                summary="No conda environment active",
                fix_hint="Run: conda activate apxm",
            )
        return CheckResult(
            name=self.name, status=CheckStatus.PASS,
            summary=f"{active.name} ({active.prefix})",
        )


class DependencyCheck:
    """Check a single tool dependency."""
    def __init__(self, spec: DependencySpec):
        self._spec = spec
        self.name = f"dep-{spec.command}"
        self.category = "deps"
        self.description = f"{spec.name} installed"

    def run(self) -> CheckResult:
        result = DependencyChecker().check(self._spec)
        if result.ok:
            return CheckResult(
                name=self.name, status=CheckStatus.PASS,
                summary=f"{result.name} {result.version}",
            )
        status = CheckStatus.FAIL if result.required else CheckStatus.WARN
        return CheckResult(
            name=self.name, status=status,
            summary=result.error or f"{result.name} not found",
            fix_hint=f"Install {result.name}",
        )


# -- Wire it all up --

def run_doctor():
    runner = DiagnosticRunner()
    runner.register(PlatformCheck())
    runner.register(CondaCheck())

    for spec in [
        DependencySpec("Rust", "rustc", min_version="1.80"),
        DependencySpec("CMake", "cmake", min_version="3.20"),
        DependencySpec("Ninja", "ninja"),
        DependencySpec("LLVM", "llvm-config"),
    ]:
        runner.register(DependencyCheck(spec))

    report = runner.run_all()
    print(TextFormatter().format(report))

    if not report.ok:
        raise SystemExit(1)
```

**Why this is better:**

- Each check is a self-contained class satisfying the `DiagnosticCheck` protocol
- The runner handles timing, error catching, and report aggregation
- Three built-in formatters: `TextFormatter`, `JsonFormatter`, `MarkdownFormatter`
- Checks can be filtered by category: `runner.run_category("deps")`
- New checks are added by registering instances -- no monolithic function to modify
- Each check is independently testable

---

## Phase 4: Shell Integration

**Module:** `sniff.shell` -- `ShellDetector`, `ShellKind`, `ActivationScriptBuilder`,
`CompletionGenerator`, `PromptHelper`, `AliasSuggestor`

### 4a. Shell-Aware Library Paths

```python
# ---------------------------------------------------------------
# BEFORE: apxm_env.py (10 lines)
# ---------------------------------------------------------------
platform_info = PlatformDetector().detect()
if platform_info.is_macos:
    env["DYLD_LIBRARY_PATH"] = ":".join(lib_paths)
else:
    env["LD_LIBRARY_PATH"] = ":".join(lib_paths)

# Generate activation script
if os.environ.get("SHELL", "").endswith("fish"):
    print(f"set -gx LD_LIBRARY_PATH {':'.join(lib_paths)}")
elif os.environ.get("SHELL", "").endswith("tcsh"):
    print(f'setenv LD_LIBRARY_PATH "{":".join(lib_paths)}"')
else:
    print(f'export LD_LIBRARY_PATH="{":".join(lib_paths)}"')


# ---------------------------------------------------------------
# AFTER: apxm_env.py (5 lines) -- 50% reduction
# ---------------------------------------------------------------
from sniff.shell import ShellDetector, ActivationScriptBuilder, ActivationConfig, EnvVar

shell = ShellDetector().detect()
config = ActivationConfig(
    env_vars=(EnvVar(name="LD_LIBRARY_PATH", value=":".join(lib_paths), prepend_path=True),),
    app_name="apxm",
)
print(ActivationScriptBuilder().build(config, shell.kind))
```

**Why this is better:**

- `ShellDetector` detects bash, zsh, fish, tcsh, PowerShell, ksh, dash, sh
  from `$SHELL`, parent process, or platform defaults
- `ActivationScriptBuilder` generates correct syntax for all shell families:
  - POSIX (bash/zsh/sh/dash/ksh): `export VAR="value"`
  - fish: `set -gx VAR value`
  - tcsh/csh: `setenv VAR "value"`
  - PowerShell: `$env:VAR = "value"`
- Includes save/restore for deactivation: `build_deactivate()`

### 4b. Tab Completion Generation

```python
# ---------------------------------------------------------------
# NEW: Generate shell completions for APXM CLI
# ---------------------------------------------------------------
from sniff.shell import CompletionGenerator, CompletionSpec, Subcommand, CommandFlag

spec = CompletionSpec(
    command="apxm",
    description="APXM agent compiler",
    flags=(
        CommandFlag(long="--verbose", short="-v", description="Verbose output"),
    ),
    subcommands=(
        Subcommand(name="build", description="Build the compiler",
                   flags=(CommandFlag(long="--release", description="Release build"),)),
        Subcommand(name="test", description="Run tests"),
        Subcommand(name="doctor", description="Check environment"),
        Subcommand(name="compile", description="Compile agent graph",
                   flags=(CommandFlag(long="--opt-level", takes_value=True,
                                     choices=("O0", "O1", "O2", "O3")),)),
    ),
)

shell = ShellDetector().detect()
print(CompletionGenerator().generate(spec, shell.kind))
# Outputs complete bash/zsh/fish/PowerShell completion script
```

---

## Phase 5: Command Registry

**Module:** `sniff.commands` -- `CommandRegistry`, `CommandMeta`, `CommandProvider`, `@command` decorator

### Before: Ad-hoc CLI Wiring

```python
# ---------------------------------------------------------------
# BEFORE: cli.py (scattered command definitions)
# ---------------------------------------------------------------
import typer

app = typer.Typer()

@app.command()
def build(release: bool = True):
    """Build APXM compiler."""
    subprocess.run(["cargo", "build"] + (["--release"] if release else []))

@app.command()
def test():
    """Run APXM test suite."""
    subprocess.run(["cargo", "test"])

@app.command()
def doctor():
    """Check environment."""
    # ... inline implementation ...

# No way to discover commands, check prerequisites, or get metadata
```

### After: Declarative Command Registry

```python
# ---------------------------------------------------------------
# AFTER: cli.py (with command registry)
# ---------------------------------------------------------------
from sniff.commands import CommandRegistry, CommandMeta, command

registry = CommandRegistry()

@command(registry, group="build", help="Build APXM compiler")
def build(release: bool = True):
    subprocess.run(["cargo", "build"] + (["--release"] if release else []))

@command(registry, group="build", help="Run APXM test suite", requires=("build",))
def test():
    subprocess.run(["cargo", "test"])

@command(registry, group="env", help="Check environment status")
def doctor():
    run_doctor()

# Or register metadata without the decorator:
registry.register(CommandMeta(
    name="compile",
    group="build",
    help="Compile an agent graph to .apxmobj",
    requires=("build",),
    tags={"tier": "core"},
))

# Discovery and introspection:
print(registry.help_summary())
# build:
#   build - Build APXM compiler
#   compile - Compile an agent graph to .apxmobj
#   test - Run APXM test suite
#
# env:
#   doctor - Check environment status

# Dependency resolution:
order = registry.resolve_order("build:test")
# ['build:build', 'build:test']

# Missing requirements:
missing = registry.missing_requirements("build:test")
# [] (all satisfied)
```

**Why this is better:**

- Commands are discoverable via `registry.all()`, `registry.by_group()`, `registry.by_tag()`
- `requires` declares prerequisites -- `resolve_order()` returns topological execution order
- `help_summary()` generates formatted help text automatically
- The `@command` decorator registers functions with zero boilerplate
- Metadata includes lifecycle hooks (`setup`, `execute`, `teardown`) and arbitrary tags
- Command status tracking: `AVAILABLE`, `DISABLED`, `DEPRECATED`

---

## New Module Reference

### Detection Modules (always succeed, never raise)

| Module | Key Classes | Lines | Purpose |
|--------|-------------|-------|---------|
| `paths` | `PathManager`, `ProjectPaths`, `ToolPath`, `LibraryPath` | 428 | Project root detection, OS-aware dirs, tool/library resolution |
| `build` | `BuildSystemDetector`, `BuildSystemInfo`, `BuildTarget` | 913 | 25 build systems from config files |
| `shell` | `ShellDetector`, `ShellKind`, `ActivationScriptBuilder`, `CompletionGenerator` | 973 | Shell detection, activation scripts, completions |
| `version` | `Version`, `VersionSpec`, `VersionConstraint` | 424 | Semver/PEP 440 parsing and constraint evaluation |
| `version_managers` | `VersionManagerDetector`, `VersionManagerInfo` | 432 | pyenv/nvm/rustup/sdkman detection |
| `toolchain` | `CMakeToolchain`, `CondaToolchain`, `EnvVarBuilder` | 172 | Composable toolchain environment profiles |
| `env` | `EnvSnapshot`, `EnvVarBuilder` | 157 | Immutable env snapshots, composable builder |
| `conda` | `CondaDetector` (enhanced), `CondaValidation` | 289 | `validate()`, `find_prefix()` added |
| `lockfile` | `LockfileParser`, `LockfileInfo`, `LockedDependency` | 639 | Lock file parsing (Cargo.lock, package-lock, etc.) |
| `cache` | `BuildCacheDetector`, `BuildCacheInfo` | 267 | Detect build cache (sccache, ccache, etc.) |
| `compiler` | Compiler detection | 291 | GCC, Clang, MSVC, rustc detection |
| `libpath` | Library path resolution | 221 | System library path detection |
| `ci_build` | CI build matrix | 119 | CI-specific build configuration |

### Framework Modules (protocol-based, consumer-implements)

| Module | Key Classes | Lines | Purpose |
|--------|-------------|-------|---------|
| `diagnostic` | `DiagnosticRunner`, `CheckRegistry`, `DiagnosticCheck` protocol | 285 | Health check framework with formatters |
| `commands` | `CommandRegistry`, `CommandMeta`, `@command` decorator | 336 | Passive command registry with dependency resolution |
| `scaffold` | `ProjectTypeDetector`, `TemplateRegistry`, `SetupScriptBuilder` | 941 | Project type detection + scaffolding |
| `validate` | Validation framework | 302 | Constraint validation |
| `remediate` | `RemediatorRegistry`, `Remediator` protocol | 165 | Issue detection + fix protocol (v1, unchanged) |

---

## Code Reduction Summary

### APXM Tooling Layer (Before vs. After)

| File | Before (lines) | After (lines) | Reduction |
|------|----------------|---------------|-----------|
| `apxm_env.py` (paths) | 17 | 5 | 71% |
| `apxm_env.py` (user dirs) | 8 | 3 | 62% |
| `apxm_env.py` (tool resolution) | 12 | 4 | 67% |
| `apxm_env.py` (MLIR setup) | 25 | 8 | 68% |
| `apxm_env.py` (shell scripts) | 10 | 5 | 50% |
| `doctor.py` (build check) | 14 | 8 | 43% |
| `doctor.py` (full doctor) | 233 | 80 | 66% |
| `deps.py` (version check) | 18 | 3 | 83% |
| **Total** | **~337** | **~116** | **~65%** |

### What Moves Into sniff

The 65% reduction in APXM code is enabled by sniff absorbing these responsibilities:

- **Path logic** (project root walking, OS directory conventions) -> `sniff.paths`
- **Build system parsing** (Cargo.toml structure, workspace detection) -> `sniff.build`
- **Toolchain env vars** (MLIR_DIR, LD_LIBRARY_PATH, platform branching) -> `sniff.toolchain`
- **Version comparison** (string parsing, semver comparison) -> `sniff.version`
- **Shell syntax** (export vs setenv vs set -gx) -> `sniff.shell`
- **Doctor infrastructure** (check running, timing, formatting, aggregation) -> `sniff.diagnostic`
- **Command metadata** (discovery, prerequisites, help generation) -> `sniff.commands`

---

## FAQ

### Does Phase 0 really require zero changes?

Yes. sniff 2.0 re-exports every symbol from v0.1.x at the same import paths.
The `__init__.py` includes all original Tier 1 exports. Bump the version
constraint in your `pyproject.toml` and run your tests.

### Can I adopt phases out of order?

Yes. Each phase is independent. The most common starting points are:

- **Phase 1** (paths) -- lowest risk, highest frequency of duplication
- **Phase 3** (diagnostics) -- highest code reduction, most architectural improvement

### What Python versions are supported?

sniff 2.0 supports Python 3.10+ (same as v0.1.x). The `tomllib` module is used
on 3.11+, with a `tomli` fallback on 3.10.

### Will sniff 2.0 add any dependencies?

No. sniff remains stdlib-only. Zero dependencies is an inviolable core principle.

### How do I test after migration?

Each phase includes a verification strategy:

- **Phase 0:** Run existing test suite unchanged
- **Phase 1-2:** Unit test the new sniff calls; integration test APXM workflows
- **Phase 3:** Each `DiagnosticCheck` is independently unit-testable
- **Phase 4-5:** Shell script output is deterministic and string-comparable

### Where is the full architecture document?

See [`ARCHITECTURE_V2.md`](./ARCHITECTURE_V2.md) in this same directory for the
complete module organization, API surface, extension points, performance design,
and release plan.
