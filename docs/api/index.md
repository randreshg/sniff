# API Reference

Sniff 2.0 organizes its API into three tiers. All public types are frozen dataclasses.
All detectors follow the "always succeeds" contract: detection methods return valid
results (with `None` fields for missing data) rather than raising exceptions.

## Tier 1: Core Detection

Stable since v0.1.0. Fully semver-protected.

| Module | Purpose | Key Types |
|--------|---------|-----------|
| [`detect`](detect.md) | Platform detection | `PlatformDetector`, `PlatformInfo` |
| [`deps`](deps.md) | Dependency checking | `DependencyChecker`, `DependencySpec`, `DependencyResult` |
| [`conda`](conda.md) | Conda environment detection | `CondaDetector`, `CondaEnvironment` |
| [`ci`](ci.md) | CI/CD provider detection | `CIDetector`, `CIInfo`, `CIProvider` |
| [`workspace`](workspace.md) | Workspace/monorepo detection | `WorkspaceDetector`, `WorkspaceInfo` |
| [`tools`](tools.md) | Tool binary checking | `ToolChecker` |
| [`config`](config.md) | Configuration management | `ConfigManager` |
| [`remediate`](remediate.md) | Remediation protocol | `Remediator`, `RemediatorRegistry` |

## Tier 2: Extended Detection

New in v2.0. Stable after v2.1.

| Module | Purpose | Key Types |
|--------|---------|-----------|
| [`paths`](paths.md) | Path resolution and project roots | `PathManager`, `ProjectPaths`, `ToolPath` |
| [`env`](env.md) | Environment variable snapshot/builder | `EnvSnapshot`, `EnvVarBuilder` |
| [`libpath`](libpath.md) | Platform-aware library path management | `LibraryPathResolver`, `LibraryPathInfo` |
| [`toolchain`](toolchain.md) | Toolchain profile composition | `ToolchainProfile`, `CMakeToolchain`, `CondaToolchain` |
| [`validate`](validate.md) | Environment validation checks | `EnvironmentValidator`, `ValidationReport` |
| [`build`](build.md) | Build system detection | `BuildSystemDetector`, `BuildSystemInfo` |
| [`compiler`](compiler.md) | Compiler detection | `CompilerDetector`, `CompilerInfo`, `ToolchainInfo` |
| [`cache`](cache.md) | Build cache detection | `BuildCacheDetector`, `BuildCacheInfo` |
| [`ci_build`](ci_build.md) | CI build hints | `CIBuildAdvisor`, `CIBuildHints` |
| [`version`](version.md) | Version parsing and constraints | `Version`, `VersionSpec`, `VersionConstraint` |
| [`shell`](shell.md) | Shell detection and script generation | `ShellDetector`, `ActivationScriptBuilder`, `CompletionGenerator` |

## Tier 3: Frameworks

Protocol-stable, implementation-flexible.

| Module | Purpose | Key Types |
|--------|---------|-----------|
| [`diagnostic`](diagnostic.md) | Diagnostic health checks | `DiagnosticRunner`, `DiagnosticCheck`, `DiagnosticReport` |
| [`diagnostic_checks`](diagnostic_checks.md) | Built-in diagnostic checks | `PlatformCheck`, `DependencyCheck`, `CIEnvironmentCheck` |
| [`commands`](commands.md) | Command/plugin registry | `CommandRegistry`, `CommandMeta`, `CommandProvider` |
| [`scaffold`](scaffold.md) | Project type detection and scaffolding | `ProjectTypeDetector`, `TemplateRegistry`, `SetupScriptBuilder` |

## Import Patterns

All public types can be imported from the top-level `sniff` package or from their
individual modules:

```python
# Top-level import (recommended)
from sniff import PlatformDetector, PathManager, CompilerDetector

# Module-level import (also supported)
from sniff.paths import PathManager, ToolPath
from sniff.compiler import CompilerDetector, CompilerFamily
```

## Design Principles

1. **Zero dependencies** -- stdlib only (Python 3.10+)
2. **Detection-only** -- never modifies state (except `LibraryPathResolver.apply()`)
3. **Frozen dataclasses** -- all result types are `@dataclass(frozen=True)`
4. **Protocol-based extensions** -- consumers implement protocols, sniff never imports consumer code
5. **Always succeeds** -- detection methods return valid results, never raise
