# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-03-10

Sniff 2.0 is a major release that transforms sniff from an "environment detection
library" into a "development environment intelligence platform." This release adds
16 new modules, over 80 new public types, and deep multi-ecosystem support -- all
while preserving full backward compatibility with the 0.1.0 API and the core
principles: zero dependencies, detection-only, frozen dataclasses, protocol-based
extensions, and always-succeeds semantics.

### Highlights

- **Build system detection** across 25 ecosystems (Cargo, CMake, npm, Poetry, Go, and more)
- **Lockfile parsing** for 7 formats (Cargo.lock, package-lock.json, yarn.lock, poetry.lock, uv.lock, pnpm-lock.yaml, Gemfile.lock)
- **Compiler and toolchain detection** for GCC, Clang, Rust, and Go with version extraction and target triples
- **Shell integration** with activation scripts, tab completions, and prompt helpers for 9 shell types
- **Semantic versioning engine** with full constraint algebra (PEP 440, semver, caret, tilde, wildcard, ranges)
- **Project scaffolding** with type detection, template registries, and setup script generation
- **Diagnostic framework** with pluggable checks, runners, and multi-format reporters
- **Environment validation** bridging detection to remediation with actionable issue reports
- **Version manager detection** for pyenv, nvm, fnm, rbenv, rustup, goenv, sdkman, asdf, and mise
- **Command registry** for passive CLI plugin systems with dependency resolution
- **Build cache detection** for sccache, ccache, Turborepo, Nx, and Bazel
- **CI build advisor** producing parallelism, caching, and output hints from CI detection
- **Path management** with project root detection, OS-aware user directories, and tool/library resolution
- **Library path resolution** with platform-aware LD_LIBRARY_PATH / DYLD_LIBRARY_PATH management
- **Environment snapshot and builder** for immutable env capture and composable construction
- **Toolchain profiles** for CMake/MLIR/LLVM and conda environment configuration

### Added

#### New Module: `sniff.build` -- Build System Detection

Pure-detection module that identifies build systems across 25 ecosystems by
scanning configuration files. No subprocess calls.

- `BuildSystem` enum -- 25 build systems: `CARGO`, `CMAKE`, `MAKE`, `MESON`, `NINJA`, `BAZEL`, `BUCK2`, `NPM`, `PNPM`, `YARN`, `BUN`, `POETRY`, `PDM`, `HATCH`, `FLIT`, `SETUPTOOLS`, `MATURIN`, `UV`, `GO`, `MAVEN`, `GRADLE`, `MIX`, `STACK`, `CABAL`, `ZIG`, `DUNE`
- `BuildTarget` dataclass -- represents a build target with `name`, `kind` (binary/library/test/bench/example/script), and optional `path`
- `BuildSystemInfo` dataclass -- detected build system with `system`, `root`, `config_file`, `version`, `targets`, `is_workspace`; includes `target_count`, `target_names`, and `targets_of_kind()` helpers
- `BuildSystemDetector` class -- `detect(root)` returns all build systems found; `detect_first(root)` returns the primary one
- Target extraction for Cargo (bin, lib, bench, example targets), CMake (add_executable, add_library), Make (phony targets), Meson (executable, library), npm/pnpm/yarn/bun (scripts), Python (PEP 621 scripts, gui-scripts), and Go (cmd/ binaries, main.go)
- Workspace detection for Cargo, npm, pnpm, yarn, bun, uv, Go, and Gradle

#### New Module: `sniff.cache` -- Build Cache Detection

Detects build cache tools via PATH lookup, environment variables, and config files.

- `CacheKind` enum -- `SCCACHE`, `CCACHE`, `TURBOREPO`, `NX`, `BAZEL`
- `BuildCacheInfo` dataclass -- `kind`, `binary_path`, `version`, `is_enabled`, `config_path`, `extra` metadata
- `BuildCacheDetector` class -- `detect_all()` finds all caches; `detect(kind)` checks a specific one
- sccache: detects S3, GCS, Azure, Redis, Memcached, and local storage backends via env vars
- ccache: detects cache directory, max size, config path, and CC/CXX wrapper usage
- Turborepo: detects remote cache (TURBO_TOKEN), team, and API endpoint
- Nx: detects Nx Cloud and custom cache directories
- Bazel: detects workspace markers, .bazelrc, and remote cache configuration

#### New Module: `sniff.ci_build` -- CI Build Advisor

Stateless advisor that produces build-system-agnostic hints from CI detection results.

- `CIBuildHints` dataclass -- `max_jobs`, `max_test_workers`, `incremental`, `use_color`, `verbose`, `ci_output`, `env_hints`
- `CIBuildAdvisor` class -- `advise()` computes parallelism caps (1 job for <=2 cores, cores for <=4, uncapped for larger), disables incremental builds in CI, enables verbose output, detects ANSI color support per provider

#### New Module: `sniff.commands` -- Command/Plugin Registry

Passive command registry for building CLI tools with dependency resolution.

- `CommandStatus` enum -- `AVAILABLE`, `DISABLED`, `DEPRECATED`
- `CommandMeta` dataclass -- `name`, `group`, `help`, `hidden`, `status`, `requires` (dependency names), `setup`/`execute`/`teardown` callables, `tags`; includes `qualified_name`, `is_available`, `has_lifecycle` properties
- `CommandProvider` protocol -- implement `commands()` to supply commands from a plugin
- `CommandRegistry` class -- `register()`, `register_all()`, `register_provider()`, `unregister()`; queries: `get()`, `all()`, `by_group()`, `groups()`, `by_status()`, `by_tag()`; dependency resolution: `missing_requirements()`, `dependents()`, `resolve_order()` (topological sort with cycle detection); documentation: `help_text()`, `help_summary()`
- `command()` decorator -- registers a function as a command with `@command(registry, group="build")`

#### New Module: `sniff.compiler` -- Compiler Detection

Detects installed compilers with version and target triple extraction via subprocess.

- `CompilerFamily` enum -- `GCC`, `CLANG`, `RUSTC`, `GO`, `UNKNOWN`
- `CompilerInfo` dataclass -- `family`, `command`, `path`, `version`, `target` triple, `language`; includes `found` property
- `ToolchainInfo` dataclass -- aggregated results with `compilers`, `default_cc`, `default_cxx`; includes `families`, `by_family()`, `by_language()` helpers
- `CompilerDetector` class -- `detect()` probes gcc, g++, clang, clang++, rustc, go; `detect_compiler(command)` probes a specific binary; detects default CC/CXX via `cc`/`c++` symlinks

#### New Module: `sniff.diagnostic` -- Diagnostic Framework

Extensible health-check system with pluggable checks and formatters.

- `CheckStatus` enum -- `PASS`, `WARN`, `FAIL`, `SKIP`
- `CheckResult` dataclass -- `name`, `status`, `summary`, `details`, `fix_hint`, `elapsed_ms`; includes `ok` property
- `DiagnosticReport` dataclass -- `results`, `elapsed_ms`; includes `passed`, `warned`, `failed`, `skipped`, `ok` aggregate properties
- `DiagnosticCheck` protocol -- implement `name`, `category`, `description`, `run()` for custom checks
- `CheckRegistry` class -- `register()`, `checks()`, `by_category()`, `categories()`
- `DiagnosticRunner` class -- `run_all()`, `run_category()`; catches exceptions from checks and attaches timing automatically
- `TextFormatter` -- plain-text report output with pass/warn/fail/skip symbols and fix hints
- `JsonFormatter` -- structured JSON output with per-check and summary sections
- `MarkdownFormatter` -- GitHub-flavored Markdown table output

#### New Module: `sniff.diagnostic_checks` -- Built-in Diagnostic Checks

Pre-built checks using existing sniff detectors, ready to register with `DiagnosticRunner`.

- `PlatformCheck` -- detects OS, architecture, container/WSL status via `PlatformDetector`
- `DependencyCheck` -- wraps a `DependencySpec` to check CLI tool availability and version requirements
- `CIEnvironmentCheck` -- detects CI/CD provider and build metadata via `CIDetector`

#### New Module: `sniff.env` -- Environment Snapshot and Builder

Immutable environment capture and composable construction.

- `EnvSnapshot` dataclass -- frozen capture of env vars as `tuple[tuple[str, str], ...]`; class methods: `capture()` (grabs live `os.environ`), `from_dict()`; query methods: `get()`, `to_dict()`, `names()`, `__contains__`, `__len__`
- `EnvVarBuilder` class -- composable builder with `set()`, `set_default()`, `set_from_path()`, `unset()`, `merge()` (from builder/snapshot/dict); terminal operations: `build()` (produces `EnvSnapshot`), `to_dict()`; all mutating methods return `self` for chaining

#### New Module: `sniff.libpath` -- Library Path Resolution

Platform-aware shared library path management.

- `LibraryPathInfo` dataclass -- `env_var`, `paths`, `platform`; includes `as_string` (platform-correct separator), `contains()` check
- `LibraryPathResolver` class -- `prepend()`, `append()`, `resolve()`, `apply()` (the one side-effecting method), `to_env_var()`, `configure_builder()`; factory methods: `for_current_platform()`, `for_platform(os_name, arch)`
- Automatic platform detection: `LD_LIBRARY_PATH` on Linux, `DYLD_LIBRARY_PATH` on macOS, `PATH` on Windows
- Deduplication across prepends, existing env, and appends

#### New Module: `sniff.lockfile` -- Lockfile Parsing

Pure-detection lockfile parser with dependency graph support. No subprocess calls.

- `LockfileKind` enum -- `CARGO`, `NPM`, `YARN`, `PNPM`, `POETRY`, `UV`, `PIP_COMPILE`, `GEMFILE`
- `LockedDependency` dataclass -- `name`, `version`, `source`, `dependencies`, `checksum`
- `LockfileInfo` dataclass -- `kind`, `path`, `lockfile_version`, `packages`; includes `package_count`, `package_names`, `get_package()`, `dependency_graph()`, `find_outdated(latest)` helpers
- `LockfileParser` class -- `parse(path)` auto-detects format from filename; `detect_and_parse(root)` scans a directory
- Full parsers for Cargo.lock (TOML + text fallback), package-lock.json (v1, v2, v3), yarn.lock (v1 classic), poetry.lock (TOML + text fallback), uv.lock (TOML), pnpm-lock.yaml (basic text parser), Gemfile.lock

#### New Module: `sniff.paths` -- Path Detection and Resolution

Project root detection, OS-aware user directories, tool and library resolution.

- `PathCategory` enum -- `PROJECT_ROOT`, `CONFIG`, `BUILD`, `SOURCE`, `TOOL`, `LIBRARY`, `DATA`, `CACHE`, `STATE`
- `ResolvedPath` dataclass -- `path`, `category`, `exists`, `label`
- `ToolPath` dataclass -- `name`, `path`, `version`; includes `found` property
- `LibraryPath` dataclass -- `name`, `lib_dir`, `include_dir`; includes `found` property
- `ProjectPaths` dataclass -- OS-aware `data_dir`, `config_dir`, `cache_dir`, `state_dir`
- `PathManager` class:
  - `find_project_root(start, markers)` -- walks up directory tree looking for `.git`, `Cargo.toml`, `pyproject.toml`, `package.json`, `go.mod`, etc.
  - `detect(root)` -- scans for config, build, and source directories
  - `user_dirs(app_name)` -- returns XDG dirs on Linux, `~/Library` on macOS, `AppData` on Windows
  - `resolve_tool(name)` -- finds a binary on PATH
  - `resolve_tools(names)` -- batch tool resolution
  - `resolve_library(name, search_paths)` -- finds lib and include directories on system paths

#### New Module: `sniff.scaffold` -- Project Scaffolding

Project type detection, template registry, and setup script generation.

- `ProjectLanguage` enum -- 15 languages: `PYTHON`, `RUST`, `JAVASCRIPT`, `TYPESCRIPT`, `GO`, `JAVA`, `CSHARP`, `CPP`, `C`, `RUBY`, `PHP`, `SWIFT`, `KOTLIN`, `SCALA`, `UNKNOWN`
- `ProjectFramework` enum -- 27 frameworks: Django, Flask, FastAPI, React, Next, Vue, Nuxt, Angular, Svelte, Express, Vite, Cargo, wasm-pack, Go modules, Maven, Gradle, SBT, CMake, Meson, Make, Autotools, Rails, Bundler, Poetry, PDM, Hatch, Flit, Maturin, Setuptools, and more
- `ProjectType` dataclass -- `language`, `framework`, `is_library`, `is_application`, `is_monorepo`, `has_tests`, `has_ci`, `has_docs`, `entry_points`
- `ProjectTypeDetector` class -- `detect(root)` identifies language from config files, refines framework from pyproject.toml build backends and package.json dependencies, detects library/app/monorepo/tests/CI/docs presence and entry points
- `FileTemplate` dataclass -- `relative_path`, `content`, `executable`, `description`
- `TemplateSet` dataclass -- named collection with `language`, `framework`, `files`, `tags`; includes `file_count`, `paths` helpers
- `TemplateProvider` protocol -- implement `get_templates(language, framework)` for custom templates
- `TemplateRegistry` class -- `register_provider()`, `register_template_set()`, `find()`, `find_by_tag()`, `all_templates`
- `SetupStep` dataclass -- `name`, `command`, `description`, `condition`, `optional`, `working_dir`
- `SetupScript` dataclass -- `name`, `description`, `steps`, `env_vars`; includes `render(shell)` for bash, fish, and PowerShell output
- `SetupScriptBuilder` class -- `build(project_type)`, `build_with_platform(project_type, os_name, pkg_manager)` with language-specific steps (Python venv, Rust/Cargo, Node.js, Go) and framework-specific additions (Poetry, PDM, Hatch, Next.js, Django, CMake)

#### New Module: `sniff.shell` -- Shell Detection and Integration

Comprehensive shell integration with activation scripts, tab completions, prompt helpers, and alias suggestions for 9 shell types.

- `ShellKind` enum -- `BASH`, `ZSH`, `FISH`, `TCSH`, `POWERSHELL`, `PWSH`, `KSH`, `DASH`, `SH`, `UNKNOWN`
- `ShellInfo` dataclass -- `kind`, `path`, `version`, `login_shell`, `is_interactive`, `config_files`; includes `is_posix`, `is_csh_family`, `is_fish`, `is_powershell`, `supports_functions` properties
- `ShellDetector` class -- detects shell from override, `$SHELL` env var, parent process (`/proc/ppid/comm`), or platform default; finds existing config files (`.bashrc`, `.zshrc`, `config.fish`, `.tcshrc`, PowerShell profiles)
- `EnvVar` dataclass -- `name`, `value`, `prepend_path` flag
- `ActivationConfig` dataclass -- `env_vars`, `path_prepends`, `app_name`, `banner`
- `ActivationScriptBuilder` class -- `build(config, shell)` and `build_deactivate(config, shell)` for POSIX (bash/zsh/sh/dash/ksh), fish, tcsh, and PowerShell; saves/restores previous values for clean deactivation
- `CommandArg`, `CommandFlag`, `Subcommand` dataclasses -- tab-completion specification types
- `CompletionSpec` dataclass -- full command structure for completion generation
- `CompletionGenerator` class -- generates completion scripts for bash (`complete -F`), zsh (`_arguments`), fish (`complete -c`), and PowerShell (`Register-ArgumentCompleter`)
- `PromptHelper` class -- `status_snippet(shell, env_var, format_str)` generates prompt integration snippets for all shell types
- `AliasSuggestor` class -- `suggest(command, subcommands, common_flags)` generates alias suggestions; `render(suggestions, shell)` produces shell-specific alias definitions

#### New Module: `sniff.toolchain` -- Toolchain Profiles

High-level environment setup abstractions that compose with `ActivationScriptBuilder`.

- `ToolchainProfile` protocol -- implement `configure(builder)` to declare env vars and paths
- `EnvVarBuilder` class (toolchain variant) -- `set_var()`, `prepend_var()`, `prepend_path()`, `set_banner()`; terminal operations: `build()` (produces `ActivationConfig`), `to_env_dict()`
- `CMakeToolchain` dataclass -- sets `MLIR_DIR`, `LLVM_DIR`, `MLIR_PREFIX`, `LLVM_PREFIX`, platform-aware library path (`LD_LIBRARY_PATH`/`DYLD_LIBRARY_PATH`), and `PATH`; accepts `extra_lib_dirs`
- `CondaToolchain` dataclass -- sets `CONDA_PREFIX`, `CONDA_DEFAULT_ENV`, and prepends `<prefix>/bin` to `PATH`

#### New Module: `sniff.validate` -- Environment Validation

Bridges detection results to the remediation system.

- `CheckStatus` enum -- `PASSED`, `WARNING`, `FAILED`, `SKIPPED`
- `CheckResult` dataclass -- `name`, `status`, `message`, `category`, `details`, `elapsed_ms`; includes `passed` property and `to_issue()` method that converts non-passing results to `DetectedIssue`
- `ValidationReport` dataclass -- `results`, `elapsed_ms`; includes `passed`, `warnings`, `failed`, `skipped`, `ok` properties and `issues()` extractor
- `EnvironmentValidator` class:
  - `add_check(fn)` -- register custom check functions
  - `check_tool(command)` -- verify a CLI tool is on PATH
  - `check_directory(path)` -- verify a directory exists
  - `check_env_var(var, expected)` -- verify an env var is set (optionally matches expected value)
  - `check_file(path)` -- verify a file exists
  - `run_all()` -- execute all registered checks; never raises
  - `run_checks(checks)` -- execute an explicit list of checks

#### New Module: `sniff.version` -- Version Constraint Engine

Full semantic versioning engine with constraint algebra. Pure data + logic, no I/O.

- `Version` dataclass -- `major`, `minor`, `patch`, `pre`, `build`; `parse()` and `try_parse()` class methods; `bump_major()`, `bump_minor()`, `bump_patch()`, `base` property; full `@total_ordering` comparison with correct pre-release semantics (1.0.0-alpha < 1.0.0)
- `ConstraintOp` enum -- `EQ` (==), `NEQ` (!=), `GTE` (>=), `GT` (>), `LTE` (<=), `LT` (<), `COMPAT` (~=), `TILDE` (~), `CARET` (^)
- `VersionConstraint` dataclass -- `op`, `version`, `satisfied_by(v)` with full caret/tilde/compatible-release semantics
- `VersionSpec` dataclass -- conjunction of constraints; `parse()` handles comma-separated constraints, wildcards (1.2.*), bare versions (treated as >=); `satisfied_by(version)`, `best_match(candidates)` (highest satisfying version)
- `compare_versions(a, b)` -- returns -1, 0, or 1
- `version_satisfies(version, spec)` -- convenience function

#### New Module: `sniff.version_managers` -- Version Manager Detection

Detects tool version managers and their managed installations.

- `ManagedVersion` dataclass -- `version`, `path`, `is_active`
- `VersionManagerInfo` dataclass -- `name`, `command`, `root`, `active_version`, `installed_versions`; includes `is_available`, `version_count` properties
- `VersionManagerDetector` class -- `detect_all()` finds all managers; `detect(name)` checks a specific one
- Supported managers: pyenv, nvm, fnm, rbenv, rustup, goenv, sdkman, asdf, mise (formerly rtx)
- Active version detection via env vars (`PYENV_VERSION`, `NVM_BIN`, `RUSTUP_TOOLCHAIN`, etc.) and command output

### Changed

#### Enhanced Module: `sniff.ci` -- CI/CD Detection (Major Expansion)

The CI module has been significantly expanded from basic provider detection to
comprehensive CI intelligence.

- **New types**: `CIGitInfo` (branch, SHA, tag, default branch), `CIPullRequest` (number, source/target branch, URL), `CIBuildInfo` (build/job/pipeline IDs, URLs), `CIRunnerInfo` (OS, arch, CPU cores, Docker availability, GPU detection, workspace path)
- **Expanded `CIInfo`**: now includes `git`, `pull_request`, `build`, `runner` fields plus `event_name`, `repository`, `server_url`; new properties `is_pr_build`, `is_tag_build`, `provider_name`
- **8 provider extractors**: GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, Travis CI, Azure Pipelines, Bitbucket Pipelines -- each with full metadata extraction
- **14 provider detection**: GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, Travis CI, Azure Pipelines, Bitbucket Pipelines, TeamCity, AWS CodeBuild, Drone CI, Woodpecker CI, Heroku CI
- **Runner capability detection**: CPU core count, Docker availability, GPU detection (NVIDIA + AMD ROCm via `/dev/nvidia0`, `/proc/driver/nvidia`, `/dev/kfd`, and env var hints)

#### Enhanced Module: `sniff.conda` -- Conda Detection (Major Expansion)

- **New type**: `CondaValidation` dataclass -- `env_name`, `found`, `prefix`, `is_active`, `missing_packages`, `errors`; includes `ok` property
- **New method**: `find_prefix(env_name, probe_common)` -- searches active env, conda/mamba commands, and common filesystem paths (`~/miniforge3`, `~/mambaforge`, `~/miniconda3`, `~/anaconda3`, `/opt/conda`)
- **New method**: `validate(env_name, required_packages)` -- validates environment existence and package availability
- `COMMON_INSTALL_PATHS` constant for fallback location probing

#### Enhanced Module: `sniff.workspace` -- Workspace Detection (Major Expansion)

- **New workspace kinds**: `UV`, `HATCH`, `PANTS`
- **New detection methods**: `_detect_uv()`, `_detect_hatch()`, `_detect_pants()`
- **New method**: `find_workspace_root(start)` -- walks up directory tree to find nearest workspace
- **Enhanced `WorkspaceInfo`**: new `build_order()` method returns topological sort of projects by internal dependencies with cycle detection

### Backward Compatibility

**Full backward compatibility is maintained.** All types and functions from sniff 0.1.0
continue to work without modification:

- `PlatformDetector`, `PlatformInfo` -- unchanged
- `DependencyChecker`, `DependencySpec`, `DependencyResult` -- unchanged
- `CondaDetector`, `CondaEnvironment` -- unchanged, with new methods added
- `ToolChecker` -- unchanged
- `ConfigManager` -- unchanged
- `CIDetector`, `CIInfo`, `CIProvider` -- unchanged, with new fields having default values
- `WorkspaceDetector`, `WorkspaceInfo`, `WorkspaceKind`, `SubProject` -- unchanged, with new enum members and methods added
- `Remediator`, `DetectedIssue`, `RemediatorRegistry` -- unchanged

The `__init__.py` re-exports all v1 types at their original import paths and adds
all v2 types. Existing `from sniff import PlatformDetector` continues to work.

### Migration Notes

#### For Existing sniff 0.1.0 Users

No migration required. All existing imports and API usage patterns work unchanged.
New features are purely additive.

#### For APXM Migration

sniff 2.0 provides direct replacements for APXM's inline environment detection:

| APXM Pattern | sniff 2.0 Replacement |
|---|---|
| Inline conda env detection | `CondaDetector.find_prefix()` + `CondaDetector.validate()` |
| Manual `setup_mlir_environment()` | `CMakeToolchain` + `CondaToolchain` + `EnvVarBuilder` |
| Inline CI detection | `CIDetector.detect()` + `CIBuildAdvisor.advise()` |
| Manual PATH manipulation | `LibraryPathResolver` or `PathManager` |
| Inline `shutil.which()` checks | `EnvironmentValidator.check_tool()` |
| Hardcoded version checks | `Version.parse()` + `VersionSpec.satisfied_by()` |
| Custom shell scripts | `ActivationScriptBuilder` + `SetupScriptBuilder` |
| Inline workspace scanning | `WorkspaceDetector.detect()` + `BuildSystemDetector.detect()` |
| Custom doctor commands | `DiagnosticRunner` + `DiagnosticCheck` protocol |
| Manual command registration | `CommandRegistry` + `@command` decorator |

### Technical Notes

- **Python support**: 3.10+ (3.11+ recommended for native `tomllib`)
- **TOML handling**: Uses `tomllib` on 3.11+, falls back to `tomli` if available, gracefully degrades to text parsing when neither is available
- **Zero dependencies**: Entire library uses only Python stdlib
- **Thread safety**: All frozen dataclasses are inherently thread-safe; mutable registries (`CommandRegistry`, `CheckRegistry`, `TemplateRegistry`) are designed for single-threaded registration followed by concurrent read-only queries
- **Side effects**: Only `LibraryPathResolver.apply()` modifies `os.environ`; all other methods are pure detection

### New Public API Summary

**26 modules** (10 existing + 16 new):

| Module | Key Types | Status |
|---|---|---|
| `detect` | `PlatformDetector`, `PlatformInfo` | Stable (v1) |
| `deps` | `DependencyChecker`, `DependencySpec`, `DependencyResult` | Stable (v1) |
| `conda` | `CondaDetector`, `CondaEnvironment`, `CondaValidation` | Stable (enhanced) |
| `tools` | `ToolChecker` | Stable (v1) |
| `config` | `ConfigManager` | Stable (v1) |
| `ci` | `CIDetector`, `CIInfo`, `CIProvider`, `CIGitInfo`, `CIPullRequest`, `CIBuildInfo`, `CIRunnerInfo` | Stable (enhanced) |
| `workspace` | `WorkspaceDetector`, `WorkspaceInfo`, `WorkspaceKind`, `SubProject` | Stable (enhanced) |
| `remediate` | `Remediator`, `DetectedIssue`, `RemediatorRegistry`, `FixResult`, `FixStatus`, `IssueSeverity` | Stable (v1) |
| `build` | `BuildSystemDetector`, `BuildSystemInfo`, `BuildSystem`, `BuildTarget` | **New** |
| `cache` | `BuildCacheDetector`, `BuildCacheInfo`, `CacheKind` | **New** |
| `ci_build` | `CIBuildAdvisor`, `CIBuildHints` | **New** |
| `commands` | `CommandRegistry`, `CommandMeta`, `CommandStatus`, `CommandProvider`, `command` | **New** |
| `compiler` | `CompilerDetector`, `CompilerInfo`, `CompilerFamily`, `ToolchainInfo` | **New** |
| `diagnostic` | `DiagnosticRunner`, `DiagnosticReport`, `CheckResult`, `CheckStatus`, `CheckRegistry`, `DiagnosticCheck`, `TextFormatter`, `JsonFormatter`, `MarkdownFormatter` | **New** |
| `diagnostic_checks` | `PlatformCheck`, `DependencyCheck`, `CIEnvironmentCheck` | **New** |
| `env` | `EnvSnapshot`, `EnvVarBuilder` | **New** |
| `libpath` | `LibraryPathResolver`, `LibraryPathInfo` | **New** |
| `lockfile` | `LockfileParser`, `LockfileInfo`, `LockfileKind`, `LockedDependency` | **New** |
| `paths` | `PathManager`, `PathCategory`, `ResolvedPath`, `ToolPath`, `LibraryPath`, `ProjectPaths` | **New** |
| `scaffold` | `ProjectTypeDetector`, `ProjectType`, `ProjectLanguage`, `ProjectFramework`, `TemplateRegistry`, `TemplateSet`, `FileTemplate`, `SetupScriptBuilder`, `SetupScript`, `SetupStep` | **New** |
| `shell` | `ShellDetector`, `ShellInfo`, `ShellKind`, `ActivationScriptBuilder`, `ActivationConfig`, `EnvVar`, `CompletionGenerator`, `CompletionSpec`, `PromptHelper`, `AliasSuggestor` | **New** |
| `toolchain` | `ToolchainProfile`, `EnvVarBuilder`, `CMakeToolchain`, `CondaToolchain` | **New** |
| `validate` | `EnvironmentValidator`, `ValidationReport`, `CheckResult`, `CheckStatus` | **New** |
| `version` | `Version`, `VersionSpec`, `VersionConstraint`, `ConstraintOp`, `compare_versions`, `version_satisfies` | **New** |
| `version_managers` | `VersionManagerDetector`, `VersionManagerInfo`, `ManagedVersion` | **New** |

## [0.1.0] - 2026-03-10

### Added

- Initial release
- `PlatformDetector` and `PlatformInfo` -- OS, architecture, Linux distro, WSL, and container detection
- `DependencyChecker`, `DependencySpec`, `DependencyResult` -- CLI tool availability and version checking
- `CondaDetector` and `CondaEnvironment` -- conda/mamba environment detection
- `ToolChecker` -- low-level tool version extraction
- `ConfigManager` -- TOML-based layered configuration (system/user/project/env)
- `CIDetector`, `CIInfo`, `CIProvider` -- CI/CD provider detection
- `WorkspaceDetector`, `WorkspaceInfo`, `WorkspaceKind`, `SubProject` -- monorepo detection
- `Remediator` protocol, `DetectedIssue`, `RemediatorRegistry` -- extension interface for remediation
- MIT License
- Project uses hatchling build backend
- Supports Python 3.10, 3.11, 3.12, 3.13

[2.0.0]: https://github.com/randreshg/sniff/compare/v0.1.0...v2.0.0
[0.1.0]: https://github.com/randreshg/sniff/releases/tag/v0.1.0
