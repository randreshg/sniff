# sniff.remediate

Extension interface for remediation -- protocols and registry for fixing detected issues.

**Module:** `sniff.remediate`
**Tier:** 1 (Core Detection)
**Side effects:** Consumer implementations may have side effects; sniff itself does not

sniff provides these types. Consumers implement them. sniff never imports or executes
any implementation.

---

## Classes

### IssueSeverity

```
enum IssueSeverity(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `INFO` | Informational, not blocking |
| `WARNING` | Works but suboptimal |
| `ERROR` | Blocking, must be fixed |

### FixStatus

```
enum FixStatus(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `FIXED` | Issue resolved |
| `PARTIAL` | Partially fixed, manual steps required |
| `SKIPPED` | Skipped (dry run or user choice) |
| `FAILED` | Fix attempt failed |

### DetectedIssue

```
@dataclass(frozen=True)
class DetectedIssue
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `category` | `str` | -- | Category (e.g., `"dependency"`, `"config"`) |
| `severity` | `IssueSeverity` | -- | How severe |
| `tool_name` | `str \| None` | -- | Tool that's missing or misconfigured |
| `message` | `str` | -- | Human-readable description |
| `details` | `dict[str, str]` | `{}` | Structured metadata |

### FixResult

```
@dataclass(frozen=True)
class FixResult
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | `FixStatus` | -- | What happened |
| `message` | `str` | -- | Description |
| `manual_steps` | `list[str]` | `[]` | Steps user must do manually |

---

## Protocols

### Remediator

```
@runtime_checkable
class Remediator(Protocol)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `name` (property) | `str` | Unique name (e.g., `"apxm-conda"`) |
| `can_fix(issue)` | `bool` | Pure check if this remediator handles the issue |
| `fix(issue, dry_run=False)` | `FixResult` | Attempt to fix. Never raises. |

---

## Classes (continued)

### RemediatorRegistry

| Method | Returns | Description |
|--------|---------|-------------|
| `register(remediator)` | `None` | Register. Raises `TypeError` if protocol not met. |
| `find_fixer(issue)` | `Remediator \| None` | First remediator that can fix the issue |
| `fix(issue, dry_run=False)` | `FixResult \| None` | Fix using registered remediators |
| `fix_all(issues, dry_run=False)` | `list[tuple[DetectedIssue, FixResult \| None]]` | Fix all issues |

---

## Examples

```python
from sniff.remediate import (
    Remediator, DetectedIssue, FixResult, FixStatus,
    IssueSeverity, RemediatorRegistry,
)

class CondaRemediator:
    @property
    def name(self) -> str:
        return "conda-installer"

    def can_fix(self, issue: DetectedIssue) -> bool:
        return issue.category == "dependency" and issue.tool_name == "cmake"

    def fix(self, issue: DetectedIssue, dry_run: bool = False) -> FixResult:
        if dry_run:
            return FixResult(status=FixStatus.SKIPPED,
                           message="Would run: conda install cmake")
        # ... actually install ...
        return FixResult(status=FixStatus.FIXED, message="Installed cmake via conda")

registry = RemediatorRegistry()
registry.register(CondaRemediator())

issue = DetectedIssue(
    category="dependency",
    severity=IssueSeverity.ERROR,
    tool_name="cmake",
    message="cmake not found",
)
result = registry.fix(issue, dry_run=True)
```
