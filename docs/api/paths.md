# sniff.paths

Path detection and resolution -- project roots, tool paths, OS-aware user directories.

**Module:** `sniff.paths`
**Tier:** 2 (Extended Detection)
**Side effects:** None

---

## Classes

### PathCategory

```
enum PathCategory(enum.Enum)
```

Category of a resolved path.

| Value | Description |
|-------|-------------|
| `PROJECT_ROOT` | Project root directory |
| `CONFIG` | Configuration directory (`.sniff/`, `.vscode/`, etc.) |
| `BUILD` | Build output directory (`target/`, `build/`, `dist/`) |
| `SOURCE` | Source directory (`src/`, `lib/`, `crates/`) |
| `TOOL` | Tool binary path |
| `LIBRARY` | Library path |
| `DATA` | Data directory |
| `CACHE` | Cache directory |
| `STATE` | State directory |

---

### ResolvedPath

```
@dataclass(frozen=True)
class ResolvedPath
```

A resolved filesystem path with metadata.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | `Path` | -- | Absolute filesystem path |
| `category` | `PathCategory` | -- | Path category |
| `exists` | `bool` | `False` | Whether the path exists on disk |
| `label` | `str` | `""` | Human-readable label |

---

### ToolPath

```
@dataclass(frozen=True)
class ToolPath
```

A resolved tool binary path.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Tool name (e.g., `"cargo"`) |
| `path` | `Path \| None` | `None` | Resolved binary path, or `None` if not found |
| `version` | `str \| None` | `None` | Tool version string |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `found` | `bool` | `True` if the tool was found on PATH |

---

### LibraryPath

```
@dataclass(frozen=True)
class LibraryPath
```

A resolved library/include path.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Library name (e.g., `"llvm"`) |
| `lib_dir` | `Path \| None` | `None` | Library directory |
| `include_dir` | `Path \| None` | `None` | Header/include directory |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `found` | `bool` | `True` if at least the lib directory was found |

---

### ProjectPaths

```
@dataclass(frozen=True)
class ProjectPaths
```

OS-aware user directory conventions (XDG on Linux, `~/Library` on macOS, `AppData` on Windows).

| Field | Type | Description |
|-------|------|-------------|
| `data_dir` | `Path` | Application data directory |
| `config_dir` | `Path` | Configuration directory |
| `cache_dir` | `Path` | Cache directory |
| `state_dir` | `Path` | State directory |

---

### PathManager

```
class PathManager
```

Detect and resolve project paths. All methods follow the sniff never-raises contract.

#### find_project_root

```python
def find_project_root(
    self,
    start: Path | None = None,
    markers: Sequence[str] | None = None,
) -> Path | None
```

Walk up from `start` to find the nearest project root. A directory is a project root
if it contains any of the `markers`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | `Path \| None` | `None` (cwd) | Starting directory |
| `markers` | `Sequence[str] \| None` | `None` | File/directory names to look for. Defaults to `.git`, `Cargo.toml`, `pyproject.toml`, `package.json`, `go.mod`, `Makefile`, `CMakeLists.txt`, `BUILD.bazel`, `WORKSPACE`, `MODULE.bazel` |

**Returns:** `Path | None` -- project root, or `None` if not found.

#### detect

```python
def detect(self, root: Path | None = None) -> tuple[ResolvedPath, ...]
```

Detect notable paths (build, source, config directories) within a project root.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | `Path \| None` | `None` | Project root. If `None`, calls `find_project_root()`. |

**Returns:** Tuple of `ResolvedPath` entries. Empty tuple if root not found.

#### user_dirs

```python
def user_dirs(self, app_name: str) -> ProjectPaths
```

Return OS-aware user directories for an application.

| Parameter | Type | Description |
|-----------|------|-------------|
| `app_name` | `str` | Application name (e.g., `"apxm"`) |

**Returns:** `ProjectPaths` with resolved directories.

**Platform behavior:**

| OS | data_dir | config_dir | cache_dir | state_dir |
|----|----------|------------|-----------|-----------|
| Linux | `$XDG_DATA_HOME/<app>` | `$XDG_CONFIG_HOME/<app>` | `$XDG_CACHE_HOME/<app>` | `$XDG_STATE_HOME/<app>` |
| macOS | `~/Library/Application Support/<app>` | `~/Library/Preferences/<app>` | `~/Library/Caches/<app>` | `~/Library/Application Support/<app>` |
| Windows | `%APPDATA%/<app>` | `%APPDATA%/<app>` | `%LOCALAPPDATA%/<app>/cache` | `%LOCALAPPDATA%/<app>` |

#### resolve_tool

```python
def resolve_tool(self, name: str) -> ToolPath
```

Resolve a tool binary on PATH using `shutil.which`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Tool name (e.g., `"cargo"`, `"cmake"`) |

**Returns:** `ToolPath` with resolved path, or `path=None` if not found.

#### resolve_tools

```python
def resolve_tools(self, names: Sequence[str]) -> tuple[ToolPath, ...]
```

Resolve multiple tool binaries. Returns one `ToolPath` per name, same order.

#### resolve_library

```python
def resolve_library(
    self,
    name: str,
    search_paths: Sequence[Path] | None = None,
) -> LibraryPath
```

Resolve a library's lib and include directories by searching standard system
paths and any additional `search_paths`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | -- | Library name (e.g., `"llvm"`, `"openssl"`) |
| `search_paths` | `Sequence[Path] \| None` | `None` | Additional directories to search |

**Returns:** `LibraryPath` with resolved directories.

---

## Examples

### Find project root

```python
from sniff import PathManager

pm = PathManager()
root = pm.find_project_root()
if root:
    print(f"Project root: {root}")

# Custom markers
root = pm.find_project_root(markers=["Cargo.toml", "tools"])
```

### Detect project paths

```python
from sniff import PathManager

pm = PathManager()
paths = pm.detect()
for p in paths:
    print(f"  [{p.category.value}] {p.label}: {p.path}")
```

### OS-aware user directories

```python
from sniff import PathManager

dirs = PathManager().user_dirs("myapp")
print(f"Config: {dirs.config_dir}")
print(f"Cache:  {dirs.cache_dir}")
```

### Resolve tools

```python
from sniff import PathManager

pm = PathManager()
cargo = pm.resolve_tool("cargo")
if cargo.found:
    print(f"cargo at {cargo.path}")

tools = pm.resolve_tools(["cmake", "ninja", "clang"])
missing = [t.name for t in tools if not t.found]
```

### Resolve libraries

```python
from sniff import PathManager
from pathlib import Path

pm = PathManager()
llvm = pm.resolve_library("llvm", search_paths=[Path("/opt/conda/envs/apxm/lib")])
if llvm.found:
    print(f"LLVM lib: {llvm.lib_dir}")
    print(f"LLVM inc: {llvm.include_dir}")
```
