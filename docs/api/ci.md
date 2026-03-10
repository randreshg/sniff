# sniff.ci

CI/CD provider detection -- identify CI environment, extract metadata, detect runner capabilities.

**Module:** `sniff.ci`
**Tier:** 1 (Core Detection)
**Side effects:** None (reads environment variables and filesystem markers only)

Supports GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, Travis CI,
Azure Pipelines, Bitbucket Pipelines, TeamCity, AWS CodeBuild, Drone CI,
Woodpecker CI, and Heroku CI.

---

## Classes

### CIProvider

```
@dataclass(frozen=True)
class CIProvider
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Machine name (e.g., `"github_actions"`) |
| `display_name` | `str` | Human name (e.g., `"GitHub Actions"`) |

### CIGitInfo

```
@dataclass(frozen=True)
class CIGitInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `branch` | `str \| None` | `None` | Current branch name |
| `commit_sha` | `str \| None` | `None` | Full commit SHA |
| `commit_short` | `str \| None` | `None` | Short SHA |
| `tag` | `str \| None` | `None` | Git tag (if tag push) |
| `default_branch` | `str \| None` | `None` | Default branch |

### CIPullRequest

```
@dataclass(frozen=True)
class CIPullRequest
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `number` | `str \| None` | `None` | PR/MR number |
| `source_branch` | `str \| None` | `None` | Source branch |
| `target_branch` | `str \| None` | `None` | Target branch |
| `url` | `str \| None` | `None` | PR/MR URL |

**Properties:** `is_pr` -- `True` if triggered by a pull request.

### CIBuildInfo

```
@dataclass(frozen=True)
class CIBuildInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `build_id` | `str \| None` | `None` | Build/run ID |
| `build_number` | `str \| None` | `None` | Build number |
| `job_id` | `str \| None` | `None` | Job ID |
| `job_name` | `str \| None` | `None` | Job name |
| `pipeline_id` | `str \| None` | `None` | Pipeline/workflow ID |
| `build_url` | `str \| None` | `None` | URL to the build |

### CIRunnerInfo

```
@dataclass(frozen=True)
class CIRunnerInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `runner_name` | `str \| None` | `None` | Runner name |
| `runner_os` | `str \| None` | `None` | Runner OS |
| `runner_arch` | `str \| None` | `None` | Runner architecture |
| `cpu_cores` | `int \| None` | `None` | Available CPU cores |
| `has_docker` | `bool` | `False` | Docker available |
| `has_gpu` | `bool` | `False` | GPU detected (NVIDIA or AMD ROCm) |
| `workspace` | `str \| None` | `None` | Workspace directory |

### CIInfo

```
@dataclass(frozen=True)
class CIInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `is_ci` | `bool` | -- | Running in any CI environment |
| `provider` | `CIProvider \| None` | `None` | Detected provider |
| `git` | `CIGitInfo` | `CIGitInfo()` | Git metadata |
| `pull_request` | `CIPullRequest` | `CIPullRequest()` | PR/MR metadata |
| `build` | `CIBuildInfo` | `CIBuildInfo()` | Build metadata |
| `runner` | `CIRunnerInfo` | `CIRunnerInfo()` | Runner capabilities |
| `event_name` | `str \| None` | `None` | Trigger event |
| `repository` | `str \| None` | `None` | Repository slug |
| `server_url` | `str \| None` | `None` | CI server URL |

**Properties:** `is_pr_build`, `is_tag_build`, `provider_name`

### CIDetector

```
class CIDetector
```

#### detect

```python
def detect(self) -> CIInfo
```

Detect CI/CD environment. Always succeeds. Returns `CIInfo(is_ci=False)` when not in CI.

---

## Examples

```python
from sniff import CIDetector

ci = CIDetector().detect()
if ci.is_ci:
    print(f"Running in {ci.provider.display_name}")
    print(f"Branch: {ci.git.branch}")
    print(f"Commit: {ci.git.commit_short}")
    if ci.is_pr_build:
        print(f"PR #{ci.pull_request.number}")
    if ci.runner.has_gpu:
        print("GPU available")
```
