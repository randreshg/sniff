# 🐕 sniff

[![Tests](https://github.com/randres/sniff/workflows/Tests/badge.svg)](https://github.com/randres/sniff/actions)
[![PyPI version](https://badge.fury.io/py/sniff.svg)](https://pypi.org/project/sniff/)
[![Python](https://img.shields.io/pypi/pyversions/sniff.svg)](https://pypi.org/project/sniff/)
[![codecov](https://codecov.io/gh/randres/sniff/branch/main/graph/badge.svg)](https://codecov.io/gh/randres/sniff)

**sniff** detects your Python development environment - platform, Python envs (conda/venv/poetry), toolchains (CMake/Rust/LLVM), and project configuration. Like a packet sniffer for networks, it's a passive observer with no side effects.

**[Documentation](https://sniff.readthedocs.io/)** • **[Source](https://github.com/randres/sniff)** • **[PyPI](https://pypi.org/project/sniff/)**

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

- **Platform detection** — OS, architecture, Linux distro, WSL, containers, CI providers
- **Python environments** — conda, venv, virtualenv, poetry, pyenv, uv, pipenv
- **Toolchain detection** — CMake, Rust, LLVM, Clang, Git, Ninja, custom tools
- **Configuration management** — TOML config with layered precedence
- **Type-safe** — Frozen dataclasses with full type hints
- **Zero dependencies** — Stdlib only (Python 3.11+)
- **Library-first** — Pure Python API, build your own CLI

---

## Documentation

Full documentation is available at **[sniff.readthedocs.io](https://sniff.readthedocs.io/)**

- [Getting Started](https://sniff.readthedocs.io/getting-started/) — Quick introduction
- [API Reference](https://sniff.readthedocs.io/api/) — Complete API docs
- [Examples](https://sniff.readthedocs.io/examples/) — Integration patterns
- [Architecture](https://sniff.readthedocs.io/architecture/) — How sniff works

---

## Real-World Usage

- **[APXM](https://github.com/yourorg/apxm)** — MLIR compiler for agent workflows
- **[Tully](https://github.com/yourorg/tully)** — Agent framework for domain workflows

*Using sniff? [Let us know!](https://github.com/randres/sniff/discussions)*

---

## Contributing

Contributions welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines.

- [Report a bug](https://github.com/randres/sniff/issues/new?template=bug_report.md)
- [Request a feature](https://github.com/randres/sniff/issues/new?template=feature_request.md)

---

## License

MIT License — see **[LICENSE](LICENSE)** for details.
