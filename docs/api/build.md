# sniff.build

Build system detection -- identify project build tools, config files, and targets.

**Module:** `sniff.build`
**Tier:** 2 (Extended Detection)
**Side effects:** None (reads files only, no subprocesses)

Detects build systems across ecosystems: Cargo, CMake, Make, Meson, Ninja, Bazel,
Buck2, npm, pnpm, yarn, bun, Poetry, PDM, Hatch, Flit, Setuptools, Maturin, uv,
Go, Maven, Gradle, Mix, Stack, Cabal, Zig, and Dune.

---

## Classes

### BuildSystem

```
enum BuildSystem(enum.Enum)
```

Known build systems.

| Value | Ecosystem |
|-------|-----------|
| `CARGO` | Rust |
| `CMAKE`, `MAKE`, `MESON`, `NINJA` | C/C++ |
| `BAZEL`, `BUCK2` | Polyglot |
| `NPM`, `PNPM`, `YARN`, `BUN` | Node.js |
| `POETRY`, `PDM`, `HATCH`, `FLIT`, `SETUPTOOLS`, `MATURIN`, `UV` | Python |
| `GO` | Go |
| `MAVEN`, `GRADLE` | Java/JVM |
| `MIX` | Elixir |
| `STACK`, `CABAL` | Haskell |
| `ZIG` | Zig |
| `DUNE` | OCaml |

---

### BuildTarget

```
@dataclass(frozen=True)
class BuildTarget
```

A build target or entry point within a project.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Target name |
| `kind` | `str` | -- | Target kind: `"binary"`, `"library"`, `"test"`, `"bench"`, `"example"`, `"script"` |
| `path` | `Path \| None` | `None` | Source file or directory for this target |

---

### BuildSystemInfo

```
@dataclass(frozen=True)
class BuildSystemInfo
```

Detected build system configuration.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `system` | `BuildSystem` | -- | Which build system |
| `root` | `Path` | -- | Project root directory |
| `config_file` | `Path` | -- | Build config file (e.g., `Cargo.toml`, `CMakeLists.txt`) |
| `version` | `str \| None` | `None` | Version constraint from config (e.g., Rust edition, CMake minimum) |
| `targets` | `tuple[BuildTarget, ...]` | `()` | Detected build targets |
| `is_workspace` | `bool` | `False` | Whether this is a workspace/monorepo root |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `target_count` | `int` | Number of targets |
| `target_names` | `tuple[str, ...]` | Names of all targets |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `targets_of_kind(kind)` | `tuple[BuildTarget, ...]` | Filter targets by kind |

---

### BuildSystemDetector

```
class BuildSystemDetector
```

Detect build systems in a project directory. A single project can use multiple
build systems (e.g., Cargo + CMake for Rust with C bindings).

#### detect

```python
def detect(self, root: Path | None = None) -> list[BuildSystemInfo]
```

Detect all build systems at the given root.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | `Path \| None` | `None` (cwd) | Directory to scan |

**Returns:** List of `BuildSystemInfo` for each detected build system. Empty list if none found.

#### detect_first

```python
def detect_first(self, root: Path | None = None) -> BuildSystemInfo | None
```

Detect the primary (first detected) build system.

---

## Detection Details

### What is detected per build system

| Build System | Config File | Targets Extracted | Workspace Detection |
|-------------|-------------|-------------------|---------------------|
| Cargo | `Cargo.toml` | `[[bin]]`, `[lib]`, `[[bench]]`, `[[example]]`, convention (`src/main.rs`, `src/lib.rs`) | `[workspace]` section |
| CMake | `CMakeLists.txt` | `add_executable()`, `add_library()` | -- |
| Make | `Makefile` / `GNUmakefile` | Rule targets (non-pattern, non-internal) | -- |
| Meson | `meson.build` | `executable()`, `library()`, `shared_library()`, `static_library()` | -- |
| Poetry | `pyproject.toml` | `[project.scripts]`, `[project.gui-scripts]` | -- |
| npm | `package.json` | `scripts` entries | `workspaces` field |
| Go | `go.mod` | `cmd/*/` directories, `main.go` | `go.work` |

### Node.js package manager priority

When multiple JS package managers are present, detection follows priority:
pnpm > yarn > bun > npm. Only the primary manager is reported.

---

## Examples

### Detect build systems

```python
from sniff.build import BuildSystemDetector

detector = BuildSystemDetector()
builds = detector.detect()
for b in builds:
    print(f"{b.system.value}: {b.config_file}")
    print(f"  Targets: {b.target_names}")
    if b.is_workspace:
        print("  (workspace)")
```

### Check for specific build system

```python
from sniff.build import BuildSystemDetector, BuildSystem

detector = BuildSystemDetector()
builds = detector.detect()
cargo = next((b for b in builds if b.system == BuildSystem.CARGO), None)
if cargo:
    bins = cargo.targets_of_kind("binary")
    print(f"Cargo binaries: {[t.name for t in bins]}")
```

### Detect primary build system

```python
from sniff.build import BuildSystemDetector

primary = BuildSystemDetector().detect_first()
if primary:
    print(f"Primary build system: {primary.system.value}")
```
