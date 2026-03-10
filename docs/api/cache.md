# sniff.cache

Build cache detection -- identify build cache tools and their configuration.

**Module:** `sniff.cache`
**Tier:** 2 (Extended Detection)
**Side effects:** None (reads environment variables and filesystem only)

Detects sccache, ccache, Turborepo, Nx, and Bazel build caches.

---

## Classes

### CacheKind

```
enum CacheKind(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `SCCACHE` | Mozilla's shared compilation cache |
| `CCACHE` | Compiler cache |
| `TURBOREPO` | Vercel monorepo build cache |
| `NX` | Nrwl monorepo build cache |
| `BAZEL` | Bazel remote/disk cache |

---

### BuildCacheInfo

```
@dataclass(frozen=True)
class BuildCacheInfo
```

Detected build cache information.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `kind` | `CacheKind` | -- | Cache type |
| `binary_path` | `str \| None` | `None` | Full path to cache binary |
| `version` | `str \| None` | `None` | Version if cheaply available |
| `is_enabled` | `bool` | `False` | Whether the cache appears actively enabled |
| `config_path` | `str \| None` | `None` | Path to config file |
| `extra` | `dict[str, str]` | `{}` | Provider-specific metadata |

---

### BuildCacheDetector

```
class BuildCacheDetector
```

Detect build cache tools in the environment. Never runs subprocesses. Never modifies state.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | `Path \| None` | `None` (cwd) | Project root for config file detection |

#### detect_all

```python
def detect_all(self) -> list[BuildCacheInfo]
```

Detect all available build caches. Returns an empty list if none are detected.

#### detect

```python
def detect(self, kind: CacheKind) -> BuildCacheInfo | None
```

Detect a specific build cache. Returns `None` if not found.

---

## Detection Details

### sccache

- **Binary:** `shutil.which("sccache")`
- **Enabled:** `RUSTC_WRAPPER` or `CC`/`CXX` contains `"sccache"`
- **Extra metadata:** Storage backend detected from env vars (`SCCACHE_BUCKET` -> S3, `SCCACHE_GCS_BUCKET` -> GCS, `SCCACHE_REDIS`, `SCCACHE_DIR` -> local, etc.)
- **Config:** `SCCACHE_CONF` env var

### ccache

- **Binary:** `shutil.which("ccache")`
- **Enabled:** `CC`/`CXX` contains `"ccache"`, or binary exists
- **Extra metadata:** `CCACHE_DIR`, `CCACHE_MAXSIZE`
- **Config:** `CCACHE_CONFIGPATH` or `~/.config/ccache/ccache.conf`

### Turborepo

- **Binary:** `shutil.which("turbo")`
- **Config:** `turbo.json` in project root
- **Extra metadata:** `TURBO_TOKEN` (remote cache), `TURBO_TEAM`, `TURBO_API`

### Nx

- **Binary:** `shutil.which("nx")`
- **Config:** `nx.json` in project root
- **Extra metadata:** `NX_CLOUD_ACCESS_TOKEN` (cloud), `NX_CACHE_DIRECTORY`

### Bazel

- **Binary:** `shutil.which("bazel")` or `shutil.which("bazelisk")`
- **Config:** `WORKSPACE`, `WORKSPACE.bazel`, or `MODULE.bazel` in project root
- **Extra metadata:** `.bazelrc` existence, `BAZEL_REMOTE_CACHE` env var

---

## Examples

### Detect all build caches

```python
from sniff.cache import BuildCacheDetector

detector = BuildCacheDetector()
caches = detector.detect_all()
for c in caches:
    status = "enabled" if c.is_enabled else "available"
    print(f"{c.kind.value}: {status}")
    if c.binary_path:
        print(f"  Binary: {c.binary_path}")
    if c.extra:
        print(f"  Extra: {c.extra}")
```

### Check for sccache

```python
from sniff.cache import BuildCacheDetector, CacheKind

detector = BuildCacheDetector()
sccache = detector.detect(CacheKind.SCCACHE)
if sccache and sccache.is_enabled:
    print(f"sccache active, storage: {sccache.extra.get('storage', 'local')}")
```
