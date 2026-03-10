# sniff.workspace

Workspace and monorepo detection.

**Module:** `sniff.workspace`
**Tier:** 1 (Core Detection)
**Side effects:** None (reads filesystem and config files only)

---

## Classes

### WorkspaceKind

```
enum WorkspaceKind(enum.Enum)
```

Types of workspace/monorepo configurations (Cargo, npm, pnpm, yarn, Go, Python, etc.).

### SubProject

```
@dataclass(frozen=True)
class SubProject
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Sub-project name |
| `path` | `Path` | Sub-project path |

### WorkspaceInfo

```
@dataclass(frozen=True)
class WorkspaceInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `kind` | `WorkspaceKind` | -- | Workspace type |
| `root` | `Path` | -- | Workspace root |
| `project_count` | `int` | `0` | Number of sub-projects |
| `projects` | `tuple[SubProject, ...]` | `()` | Sub-project list |

### WorkspaceDetector

```
class WorkspaceDetector
```

#### detect

```python
def detect(self, root: Path) -> list[WorkspaceInfo]
```

Detect all workspace configurations at the given root.

#### detect_first

```python
def detect_first(self, root: Path) -> WorkspaceInfo | None
```

Detect the primary workspace configuration.

---

## Examples

```python
from sniff import WorkspaceDetector
from pathlib import Path

detector = WorkspaceDetector()
workspaces = detector.detect(Path.cwd())
for ws in workspaces:
    print(f"{ws.kind.value} workspace ({ws.project_count} projects)")
    for p in ws.projects:
        print(f"  - {p.name}: {p.path}")
```
