# 🐕 sniff

[![Tests](https://github.com/randreshg/sniff/workflows/Tests/badge.svg)](https://github.com/randreshg/sniff/actions)
[![PyPI version](https://badge.fury.io/py/sniff.svg)](https://pypi.org/project/sniff/)
[![Python](https://img.shields.io/pypi/pyversions/sniff.svg)](https://pypi.org/project/sniff/)
[![codecov](https://codecov.io/gh/randreshg/sniff/branch/main/graph/badge.svg)](https://codecov.io/gh/randreshg/sniff)

**sniff** detects your Python development environment - platform, Python envs (conda/venv/poetry), toolchains (CMake/Rust/LLVM), and project configuration. Like a packet sniffer for networks, it's a passive observer with no side effects.

**[Documentation](https://sniff.readthedocs.io/)** • **[Source](https://github.com/randreshg/sniff)** • **[PyPI](https://pypi.org/project/sniff/)**

---

## Installation

```bash
pip install sniff
```

---

## Quick Start

### Detect Platform

```python
import sniff

platform = sniff.PlatformDetector().detect()
print(f"{platform.os} {platform.arch}")  # Linux x86_64
print(f"WSL: {platform.is_wsl}")         # False
```

### Check Dependencies

```python
from sniff import DependencyChecker, DependencySpec

checker = DependencyChecker()
rust = checker.check(DependencySpec("Rust", "rustc", min_version="1.70"))

print(f"Rust {rust.version}: {'✓' if rust.ok else '✗'}")
```

### Find Python Environments

```python
from sniff import CondaDetector

conda = CondaDetector()
env = conda.find_active()
if env:
    print(f"Active: {env.name} at {env.prefix}")
```

---

## Features

### Core Detection (Tier 1)

- **Platform detection** — OS, architecture, Linux distro, WSL, containers, CI providers
- **Python environments** — conda, venv, virtualenv, poetry, pyenv, uv, pipenv
- **Dependency checking** — verify CLI tool availability and version constraints
- **Workspace detection** — monorepo/workspace structure detection
- **Configuration management** — TOML config with layered precedence
- **Remediation framework** — protocol-based fix system for detected issues

### Extended Detection (Tier 2 -- new in 2.0)

- **Path management** — project root detection, OS-aware user directories, tool/library resolution
- **Build system detection** — Cargo, CMake, Make, npm, Poetry, Go, and 20+ more
- **Compiler detection** — GCC, Clang, Rust, Go with version and target triple extraction
- **Build cache detection** — sccache, ccache, Turborepo, Nx, Bazel
- **Shell integration** — detection, activation scripts, tab completions, prompt helpers
- **Library path management** — platform-aware LD_LIBRARY_PATH / DYLD_LIBRARY_PATH
- **Toolchain profiles** — composable environment setup for CMake/LLVM, Conda, custom toolchains
- **Version management** — semver parsing, constraint validation, range matching
- **Environment validation** — check tools, directories, env vars with structured reports
- **CI build hints** — parallelism, caching, and output recommendations for CI runners

### Frameworks (Tier 3 -- new in 2.0)

- **Diagnostic framework** — extensible health checks with pluggable formatters (text, JSON, Markdown)
- **Command registry** — passive command/plugin registry with dependency resolution
- **Project scaffolding** — project type detection, template system, setup script generation

### Design

- **Type-safe** — Frozen dataclasses with full type hints
- **Zero dependencies** — Stdlib only (Python 3.10+)
- **Library-first** — Pure Python API, build your own CLI

---

## Documentation

- [Getting Started](docs/getting-started.md) — Quick introduction
- [API Reference](docs/api/index.md) — Complete API docs for all modules
- [Architecture](docs/ARCHITECTURE_V2.md) — How sniff 2.0 works

### API Reference by Module

**Core:** [detect](docs/api/detect.md) | [deps](docs/api/deps.md) | [conda](docs/api/conda.md) | [ci](docs/api/ci.md) | [workspace](docs/api/workspace.md) | [tools](docs/api/tools.md) | [config](docs/api/config.md) | [remediate](docs/api/remediate.md)

**Extended:** [paths](docs/api/paths.md) | [env](docs/api/env.md) | [libpath](docs/api/libpath.md) | [toolchain](docs/api/toolchain.md) | [validate](docs/api/validate.md) | [build](docs/api/build.md) | [compiler](docs/api/compiler.md) | [cache](docs/api/cache.md) | [ci_build](docs/api/ci_build.md) | [version](docs/api/version.md) | [shell](docs/api/shell.md)

**Frameworks:** [diagnostic](docs/api/diagnostic.md) | [diagnostic_checks](docs/api/diagnostic_checks.md) | [commands](docs/api/commands.md) | [scaffold](docs/api/scaffold.md)

---

## Real-World Usage

- **[APXM](https://github.com/yourorg/apxm)** — MLIR compiler for agent workflows
- **[Tully](https://github.com/yourorg/tully)** — Agent framework for domain workflows

*Using sniff? [Let us know!](https://github.com/randreshg/sniff/discussions)*

---

## Contributing

Contributions welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines.

- [Report a bug](https://github.com/randreshg/sniff/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/randreshg/sniff/issues/new?template=feature_request.md)

---

## License

MIT License — see **[LICENSE](LICENSE)** for details.
