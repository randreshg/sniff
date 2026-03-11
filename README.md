# sniff

[![Tests](https://github.com/randreshg/sniff/workflows/Tests/badge.svg)](https://github.com/randreshg/sniff/actions)
[![PyPI version](https://img.shields.io/pypi/v/sniff?color=blue)](https://pypi.org/project/sniff/)
[![Python](https://img.shields.io/pypi/pyversions/sniff.svg)](https://pypi.org/project/sniff/)
[![codecov](https://codecov.io/gh/randreshg/sniff/branch/main/graph/badge.svg)](https://codecov.io/gh/randreshg/sniff)

**sniff: The environment-aware CLI framework for Python**

Detect your development environment -- platform, Python envs, toolchains, hardware -- then build polished CLIs on top of it. Like a packet sniffer for networks, sniff is a passive observer with no side effects.

**[Documentation](https://sniff.readthedocs.io/)** | **[Source](https://github.com/randreshg/sniff)** | **[PyPI](https://pypi.org/project/sniff/)**

---

### What's New in v3.0.0

sniff 3.0 graduates from a detection library into a full **CLI framework**. Everything you need to build production-quality command-line tools -- styling, structured errors, progress indicators, multi-format output, and configuration management -- ships as a cohesive toolkit built on Rich and Typer.

- **`sniff.cli.styles`** -- 12 semantic output functions (`print_success`, `print_error`, `print_table`, ...) covering 89% of real-world CLI output patterns
- **`sniff.cli.errors`** -- Structured error hierarchy with exit codes, hints, and JSON/YAML serialization
- **`sniff.cli.progress`** -- Progress bars, spinners, and multi-step `StatusReporter` for long-running operations
- **`sniff.cli.output`** -- `OutputFormatter` with TABLE, JSON, YAML, and TEXT output modes plus quiet/verbose support
- **`sniff.cli.config`** -- `ConfigManager` with TOML support and multi-tier precedence (env vars > project > user > defaults)
- **`sniff.cli.context`** -- `CLIContext` dataclass for shared command state via `typer.Context.obj`
- **Zero-dependency core preserved** -- CLI features are optional via `pip install sniff[cli]`

---

## Installation

```bash
# Core library (zero dependencies, Python 3.10+)
pip install sniff

# With CLI framework support (adds typer + rich)
pip install sniff[cli]

# With experiment tracking (adds tully)
pip install sniff[tracking]

# Everything
pip install sniff[all]
```

The `[cli]` extra is required for `sniff.cli.*`, `sniff.Typer`, and all Rich-based output. The core detection API remains dependency-free.

---

## Quick Start

### Detect Your Environment

```python
import sniff

platform = sniff.PlatformDetector().detect()
print(f"{platform.os} {platform.arch}")  # Linux x86_64
print(f"WSL: {platform.is_wsl}")         # False
```

### Build a CLI with Styled Output

```python
from sniff.cli.styles import print_success, print_error, print_warning, print_header

print_header("Build Pipeline", subtitle="v3.0.0")
print_success("Compiled 42 modules")
print_warning("3 deprecation warnings")
print_error("Failed to link libfoo.so")
```

### Multi-Format Output (Table / JSON / YAML)

```python
from sniff.cli.output import OutputFormatter, OutputFormat

fmt = OutputFormatter(format=OutputFormat.TABLE, verbose=True)
fmt.print_result(
    {"name": "myapp", "version": "1.2.0", "env": "conda:ml"},
    title="Package Info",
)
fmt.success("Environment validated")

# Switch to JSON for piping to other tools
fmt_json = OutputFormatter(format=OutputFormat.JSON)
fmt_json.print_result({"name": "myapp", "version": "1.2.0"})
# {"name": "myapp", "version": "1.2.0"}
```

### Progress Indicators

```python
from sniff.cli.progress import progress_bar, spinner, StatusReporter

# Deterministic progress bar
with progress_bar("Compiling modules", total=100) as progress:
    task = progress.tasks[0]
    for i in range(100):
        progress.update(task.id, advance=1)

# Indeterminate spinner
with spinner("Resolving dependencies..."):
    resolve_all()

# Multi-step status reporting
reporter = StatusReporter("Deployment")
reporter.start("Checking prerequisites")
reporter.success("All prerequisites met")
reporter.start("Uploading artifacts")
reporter.warning("Slow network detected")
reporter.success("Upload complete")
```

### Error Handling with SniffError

```python
from sniff.cli.errors import NotFoundError, SniffError
from sniff.cli.styles import print_error, print_info

try:
    raise NotFoundError(
        "Conda environment 'ml' not found",
        hint="Run 'conda create -n ml' to create it",
        searched_paths=["/opt/conda/envs", "~/.conda/envs"],
    )
except SniffError as exc:
    print_error(exc.message)
    if exc.hint:
        print_info(f"Hint: {exc.hint}")
    raise SystemExit(exc.exit_code)
```

All errors carry an `exit_code`, an optional `hint`, and a `to_dict()` method for structured output.

### ConfigManager

```python
from sniff.cli.config import ConfigManager

# Loads from ~/.myapp/config.toml, .myapp/config.toml, and env vars
cfg = ConfigManager("myapp", defaults={"database": {"path": "db.sqlite"}})

print(cfg.get("database.path"))    # db.sqlite
cfg.set("database.path", "/data/prod.sqlite")
cfg.save()                         # writes to ~/.myapp/config.toml
```

Precedence (highest wins): environment variables (`MYAPP_DATABASE_PATH`) > project config (`.myapp/config.toml`) > user config (`~/.myapp/config.toml`) > built-in defaults.

---

## CLI Framework

The `sniff.cli` package provides everything needed to build consistent, production-quality CLIs.

### sniff.Typer -- Enhanced Typer Wrapper

Drop-in replacement for `typer.Typer` with automatic environment detection, session hooks, and built-in commands.

```python
import sniff

app = sniff.Typer(
    name="myapp",
    project_version="1.0.0",
    add_version_command=True,
    add_doctor_command=True,
    add_env_command=True,
)

@app.command()
def build(target: str = "release"):
    """Build the project."""
    from sniff.cli.styles import print_success
    print_success(f"Built target: {target}")

    # Access detected environment
    print(f"Platform: {app.platform.os}")
    if app.conda_env:
        print(f"Conda: {app.conda_env.name}")

if __name__ == "__main__":
    app()
```

Built-in commands (opt-in): `doctor` (health checks), `version` (version + environment), `env` (full environment dump).

### CLIContext -- Shared Command State

```python
import typer
from sniff.cli.context import CLIContext
from sniff.cli.config import ConfigManager
from sniff.cli.output import OutputFormatter, OutputFormat

app = typer.Typer()

@app.callback()
def main(ctx: typer.Context, verbose: bool = False, output: str = "table"):
    ctx.obj = CLIContext(
        config=ConfigManager("myapp"),
        output=OutputFormatter(format=OutputFormat(output), verbose=verbose),
        verbose=verbose,
    )

@app.command()
def status(ctx: typer.Context):
    cli: CLIContext = ctx.obj
    cli.output.print_result({"status": "healthy"}, title="System Status")
```

### Styling Reference

| Function | Purpose |
|---|---|
| `print_success(msg)` | Green checkmark + message |
| `print_error(msg)` | Red X + message (stderr) |
| `print_warning(msg)` | Warning icon + message (stderr) |
| `print_info(msg)` | Info icon + message |
| `print_debug(msg)` | Dimmed message |
| `print_header(title, subtitle)` | Bordered panel |
| `print_step(msg, step_num, total)` | Step indicator `[1/5]` |
| `print_section(title)` | Section divider |
| `print_table(title, headers, rows)` | Rich table |
| `print_numbered_list(items)` | Numbered list |
| `print_next_steps(steps)` | "Next steps:" block |

### Error Hierarchy

| Exception | Exit Code | Use Case |
|---|---|---|
| `SniffError` | 1 | Base class |
| `ValidationError` | 2 | Invalid input or data |
| `NotFoundError` | 3 | Missing resource |
| `PermissionError` | 4 | Insufficient permissions |
| `TimeoutError` | 5 | Operation timed out |
| `ConfigError` | 6 | Bad configuration |
| `DependencyError` | 7 | Missing dependency |
| `RuntimeError` | 8 | Execution failure |

---

## Environment Detection

### Core Detection (Tier 1)

- **Platform detection** -- OS, architecture, Linux distro, WSL, containers, CI providers
- **Python environments** -- conda, venv, virtualenv, poetry, pyenv, uv, pipenv
- **Dependency checking** -- verify CLI tool availability and version constraints
- **Workspace detection** -- monorepo/workspace structure detection
- **Configuration management** -- TOML config with layered precedence
- **Remediation framework** -- protocol-based fix system for detected issues

### Extended Detection (Tier 2)

- **Path management** -- project root detection, OS-aware user directories, tool/library resolution
- **Build system detection** -- Cargo, CMake, Make, npm, Poetry, Go, and 20+ more
- **Compiler detection** -- GCC, Clang, Rust, Go with version and target triple extraction
- **Build cache detection** -- sccache, ccache, Turborepo, Nx, Bazel
- **Shell integration** -- detection, activation scripts, tab completions, prompt helpers
- **Library path management** -- platform-aware LD_LIBRARY_PATH / DYLD_LIBRARY_PATH
- **Toolchain profiles** -- composable environment setup for CMake/LLVM, Conda, custom toolchains
- **Version management** -- semver parsing, constraint validation, range matching
- **Environment validation** -- check tools, directories, env vars with structured reports
- **CI build hints** -- parallelism, caching, and output recommendations for CI runners

### Frameworks (Tier 3)

- **Diagnostic framework** -- extensible health checks with pluggable formatters (text, JSON, Markdown)
- **Command registry** -- passive command/plugin registry with dependency resolution
- **Project scaffolding** -- project type detection, template system, setup script generation

### ExecutionContext

Capture your entire execution environment in a single call with fingerprinting and diffing for reproducibility.

```python
from sniff import ExecutionContext

ctx = ExecutionContext.capture()
print(ctx.platform)           # PlatformInfo(os='Linux', arch='x86_64', ...)
print(ctx.fingerprint())      # sha256 reproducibility hash

# Later, compare environments
ctx2 = ExecutionContext.capture()
diff = ctx.diff(ctx2)
if not diff.is_compatible():
    print(diff.summary())
```

### Design Principles

- **Type-safe** -- Frozen dataclasses with full type hints
- **Zero dependencies** -- Core is stdlib only (Python 3.10+)
- **Optional extras** -- CLI features via `sniff[cli]`, tracking via `sniff[tracking]`
- **Library-first** -- Pure Python API, build your own CLI

---

## Documentation

- [Getting Started](docs/getting-started.md) -- Quick introduction
- [API Reference](docs/api/index.md) -- Complete API docs for all modules
- [Architecture](docs/ARCHITECTURE_V2.md) -- How sniff works internally

### CLI Framework (New in 3.0)

- [ExecutionContext API](docs/EXECUTIONCONTEXT.md) -- Complete environment capture
- [sniff.Typer Guide](docs/TYPER_INTEGRATION.md) -- CLI framework integration
- [Migration Guide](docs/MIGRATION_2.1.md) -- Upgrading from earlier versions
- [Examples](docs/EXAMPLES.md) -- APXM, Tully, and more

### API Reference by Module

**Core:** [detect](docs/api/detect.md) | [deps](docs/api/deps.md) | [conda](docs/api/conda.md) | [ci](docs/api/ci.md) | [workspace](docs/api/workspace.md) | [tools](docs/api/tools.md) | [config](docs/api/config.md) | [remediate](docs/api/remediate.md)

**Extended:** [paths](docs/api/paths.md) | [env](docs/api/env.md) | [libpath](docs/api/libpath.md) | [toolchain](docs/api/toolchain.md) | [validate](docs/api/validate.md) | [build](docs/api/build.md) | [compiler](docs/api/compiler.md) | [cache](docs/api/cache.md) | [ci_build](docs/api/ci_build.md) | [version](docs/api/version.md) | [shell](docs/api/shell.md)

**Frameworks:** [diagnostic](docs/api/diagnostic.md) | [diagnostic_checks](docs/api/diagnostic_checks.md) | [commands](docs/api/commands.md) | [scaffold](docs/api/scaffold.md)

---

## Real-World Usage

- **[APXM](https://github.com/yourorg/apxm)** -- MLIR compiler for agent workflows
- **[Tully](https://github.com/yourorg/tully)** -- Agent framework for domain workflows

*Using sniff? [Let us know!](https://github.com/randreshg/sniff/discussions)*

---

## Contributing

Contributions welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines.

- [Report a bug](https://github.com/randreshg/sniff/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/randreshg/sniff/issues/new?template=feature_request.md)

---

## License

MIT License -- see **[LICENSE](LICENSE)** for details.
