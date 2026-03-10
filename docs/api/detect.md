# sniff.detect

Platform detection -- OS, architecture, Linux distro, WSL, containers.

**Module:** `sniff.detect`
**Tier:** 1 (Core Detection)
**Side effects:** None (reads `/etc/os-release`, env vars, and filesystem markers)

---

## Classes

### PlatformInfo

```
@dataclass(frozen=True)
class PlatformInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `os` | `str` | -- | Operating system: `"Linux"`, `"Darwin"`, `"Windows"` |
| `arch` | `str` | -- | CPU architecture: `"x86_64"`, `"aarch64"`, `"arm64"` |
| `distro` | `str \| None` | `None` | Linux distro ID (e.g., `"ubuntu"`, `"fedora"`) |
| `distro_version` | `str \| None` | `None` | Distro version string |
| `distro_name` | `str \| None` | `None` | Distro display name |
| `pkg_manager` | `str \| None` | `None` | Detected package manager: `"apt"`, `"dnf"`, `"brew"`, `"pacman"` |
| `is_wsl` | `bool` | `False` | Running under Windows Subsystem for Linux |
| `is_container` | `bool` | `False` | Running in a container (Docker, Podman, etc.) |
| `is_macos` | `bool` | `False` | Running on macOS |
| `is_windows` | `bool` | `False` | Running on Windows |

### PlatformDetector

```
class PlatformDetector
```

#### detect

```python
def detect(self) -> PlatformInfo
```

Detect the current platform. Always succeeds.

---

## Examples

```python
from sniff import PlatformDetector

platform = PlatformDetector().detect()
print(f"{platform.os} {platform.arch}")
print(f"Distro: {platform.distro} {platform.distro_version}")
print(f"WSL: {platform.is_wsl}, Container: {platform.is_container}")
print(f"Package manager: {platform.pkg_manager}")
```
