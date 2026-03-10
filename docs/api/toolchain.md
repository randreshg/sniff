# sniff.toolchain

Toolchain profiles -- high-level abstractions for environment setup.

**Module:** `sniff.toolchain`
**Tier:** 2 (Extended Detection)
**Side effects:** None

A toolchain profile declares which environment variables, PATH entries, and library
paths are needed for a particular toolchain. The `EnvVarBuilder` collects declarations
from multiple profiles and produces an `ActivationConfig` for the `ActivationScriptBuilder`.

---

## Protocols

### ToolchainProfile

```
@runtime_checkable
class ToolchainProfile(Protocol)
```

Protocol for toolchain environment configuration. Implementors declare what
environment variables and paths they need by calling methods on the provided
`EnvVarBuilder`.

| Method | Description |
|--------|-------------|
| `configure(builder: EnvVarBuilder) -> None` | Populate builder with required env vars and paths |

---

## Classes

### EnvVarBuilder

```
class EnvVarBuilder
```

Accumulates environment variable declarations from toolchain profiles. Call
`configure` on one or more `ToolchainProfile` instances, then call `build()`
to get a frozen `ActivationConfig`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_name` | `str` | `""` | Application name (used in activation script comments) |

#### Methods

| Method | Description |
|--------|-------------|
| `set_var(name, value)` | Set an environment variable unconditionally |
| `prepend_var(name, value)` | Prepend value to existing variable (colon-separated) |
| `prepend_path(directory)` | Prepend a directory to `PATH` |
| `set_banner(banner)` | Set the activation banner message |
| `build()` | Produce a frozen `ActivationConfig` |
| `to_env_dict()` | Produce a plain dict for `subprocess.Popen` |

---

### CMakeToolchain

```
@dataclass(frozen=True)
class CMakeToolchain
```

CMake / MLIR / LLVM toolchain rooted at a conda (or system) prefix.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prefix` | `Path` | -- | Root directory (e.g., conda env prefix) |
| `extra_lib_dirs` | `tuple[str, ...]` | `()` | Additional library directories to prepend |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `mlir_dir` | `Path` | `<prefix>/lib/cmake/mlir` |
| `llvm_dir` | `Path` | `<prefix>/lib/cmake/llvm` |
| `lib_dir` | `Path` | `<prefix>/lib` |
| `bin_dir` | `Path` | `<prefix>/bin` |

**configure() sets:**
- `MLIR_DIR` -> `<prefix>/lib/cmake/mlir`
- `LLVM_DIR` -> `<prefix>/lib/cmake/llvm`
- `MLIR_PREFIX` -> `<prefix>`
- `LLVM_PREFIX` -> `<prefix>`
- `LD_LIBRARY_PATH` (Linux) or `DYLD_LIBRARY_PATH` (macOS) prepended with `<prefix>/lib`
- `PATH` prepended with `<prefix>/bin`

---

### CondaToolchain

```
@dataclass(frozen=True)
class CondaToolchain
```

Conda environment toolchain.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prefix` | `Path` | -- | Conda environment prefix |
| `env_name` | `str` | `""` | Environment name (optional) |

**configure() sets:**
- `CONDA_PREFIX` -> `<prefix>`
- `CONDA_DEFAULT_ENV` -> `<env_name>` (if provided)
- `PATH` prepended with `<prefix>/bin`

---

## Examples

### Compose multiple toolchains

```python
from pathlib import Path
from sniff.toolchain import CMakeToolchain, CondaToolchain, EnvVarBuilder
from sniff.shell import ActivationScriptBuilder, ShellKind

conda = CondaToolchain(prefix=Path("/opt/conda/envs/apxm"))
cmake = CMakeToolchain(prefix=Path("/opt/conda/envs/apxm"))

builder = EnvVarBuilder(app_name="apxm")
conda.configure(builder)
cmake.configure(builder)

config = builder.build()
script = ActivationScriptBuilder().build(config, ShellKind.BASH)
print(script)
```

### Custom toolchain profile

```python
from pathlib import Path
from sniff.toolchain import EnvVarBuilder

class ROCmToolchain:
    """Custom toolchain for AMD ROCm."""

    def __init__(self, rocm_path: Path):
        self.rocm_path = rocm_path

    def configure(self, builder: EnvVarBuilder) -> None:
        builder.set_var("ROCM_PATH", str(self.rocm_path))
        builder.set_var("HIP_PATH", str(self.rocm_path))
        builder.prepend_var("LD_LIBRARY_PATH", str(self.rocm_path / "lib"))
        builder.prepend_path(self.rocm_path / "bin")

# Use it
builder = EnvVarBuilder(app_name="myapp")
ROCmToolchain(Path("/opt/rocm")).configure(builder)
env_dict = builder.to_env_dict()
```

### Get env dict for subprocess

```python
import subprocess
from sniff.toolchain import CMakeToolchain, EnvVarBuilder

builder = EnvVarBuilder()
CMakeToolchain(prefix=Path("/opt/llvm")).configure(builder)

# Merge with current env for subprocess
import os
env = {**os.environ, **builder.to_env_dict()}
subprocess.run(["cmake", "--build", "build"], env=env)
```
