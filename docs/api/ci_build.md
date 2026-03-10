# sniff.ci_build

CI build hints -- advise on parallelism, caching, and output settings for CI runners.

**Module:** `sniff.ci_build`
**Tier:** 2 (Extended Detection)
**Side effects:** None (pure computation from `CIInfo`)

Takes `CIInfo` from `sniff.ci` and produces build-system-agnostic hints for
parallelism capping, incremental build recommendations, and output formatting.

---

## Classes

### CIBuildHints

```
@dataclass(frozen=True)
class CIBuildHints
```

Build-system-agnostic hints for CI environments. All fields are advisory --
consumers decide how to map these to their specific build system.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_jobs` | `int \| None` | `None` | Recommended max parallel jobs (`None` = no cap) |
| `max_test_workers` | `int \| None` | `None` | Recommended max test parallelism |
| `incremental` | `bool` | `True` | Whether incremental builds are recommended |
| `use_color` | `bool` | `False` | Whether color output is safe |
| `verbose` | `bool` | `False` | Whether verbose output is recommended |
| `ci_output` | `bool` | `False` | Suppress progress bars/spinners |
| `env_hints` | `dict[str, str]` | `{}` | Recommended environment variable overrides |

---

### CIBuildAdvisor

```
class CIBuildAdvisor
```

Produce build hints from a `CIInfo` detection result.

| Parameter | Type | Description |
|-----------|------|-------------|
| `ci` | `CIInfo` | CI detection result from `CIDetector().detect()` |

#### advise

```python
def advise(self) -> CIBuildHints
```

Compute build hints for the detected CI environment.

**Local (non-CI) defaults:**
- `incremental=True`, no parallelism cap, no special output settings

**CI behavior:**
- Parallelism capped on small runners (<=2 cores -> 1 job, <=4 -> cores)
- `incremental=False` (CI builds are clean builds)
- `verbose=True`
- `ci_output=True`
- Color enabled for providers that support ANSI (GitHub Actions, GitLab CI, Buildkite, CircleCI)
- `FORCE_COLOR=1` added to `env_hints` when color is supported

---

## Examples

### Get build hints

```python
from sniff.ci import CIDetector
from sniff.ci_build import CIBuildAdvisor

ci = CIDetector().detect()
hints = CIBuildAdvisor(ci).advise()

if hints.max_jobs:
    print(f"Limit parallelism to {hints.max_jobs} jobs")
if hints.ci_output:
    print("Suppress progress bars")
if hints.use_color:
    print("ANSI color is safe")
```

### Apply hints to Cargo build

```python
from sniff.ci import CIDetector
from sniff.ci_build import CIBuildAdvisor

ci = CIDetector().detect()
hints = CIBuildAdvisor(ci).advise()

cargo_args = ["cargo", "build"]
if hints.max_jobs:
    cargo_args.extend(["--jobs", str(hints.max_jobs)])
if not hints.incremental:
    cargo_args.append("--release")
if hints.use_color:
    cargo_args.extend(["--color", "always"])
```

### Apply hints to CMake

```python
from sniff.ci import CIDetector
from sniff.ci_build import CIBuildAdvisor

ci = CIDetector().detect()
hints = CIBuildAdvisor(ci).advise()

cmake_args = ["cmake", "--build", "build"]
if hints.max_jobs:
    cmake_args.extend(["-j", str(hints.max_jobs)])
if hints.verbose:
    cmake_args.append("--verbose")
```
