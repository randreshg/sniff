# sniff.shell

Shell detection and integration -- identify shell, generate activation scripts,
tab-completion scripts, prompt integration, and alias suggestions.

**Module:** `sniff.shell`
**Tier:** 2 (Extended Detection)
**Side effects:** None (detection reads env vars and filesystem; script generation produces strings)

---

## Shell Detection

### ShellKind

```
enum ShellKind(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `BASH` | Bourne Again Shell |
| `ZSH` | Z Shell |
| `FISH` | Friendly Interactive Shell |
| `TCSH` | TENEX C Shell |
| `POWERSHELL` | Windows PowerShell |
| `PWSH` | PowerShell Core (cross-platform) |
| `KSH` | KornShell |
| `DASH` | Debian Almquist Shell |
| `SH` | Bourne shell / generic POSIX |
| `UNKNOWN` | Unknown shell |

### ShellInfo

```
@dataclass(frozen=True)
class ShellInfo
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `kind` | `ShellKind` | -- | Detected shell type |
| `path` | `str \| None` | `None` | Absolute path to shell binary |
| `version` | `str \| None` | `None` | Shell version string |
| `login_shell` | `str \| None` | `None` | User's login shell from `SHELL` |
| `is_interactive` | `bool` | `False` | Likely running interactively |
| `config_files` | `tuple[str, ...]` | `()` | Existing rc/profile files |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_posix` | `bool` | Uses POSIX syntax (`export`, `$VAR`) -- bash, zsh, ksh, dash, sh |
| `is_csh_family` | `bool` | Uses csh syntax (`setenv`) -- tcsh |
| `is_fish` | `bool` | Fish shell |
| `is_powershell` | `bool` | PowerShell or PowerShell Core |
| `supports_functions` | `bool` | Supports function definitions |

### ShellDetector

```
class ShellDetector
```

Detect the current shell environment.

**Detection strategy (priority order):**
1. Explicit override via `shell_override` argument
2. `SHELL` environment variable
3. Parent process name heuristic (`/proc/<ppid>/comm` on Linux)
4. Platform default fallback (PowerShell on Windows, sh on Unix)

```python
def detect(self, shell_override: str | None = None) -> ShellInfo
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `shell_override` | `str \| None` | `None` | Force a specific shell (name or path) |

---

## Activation Scripts

### EnvVar

```
@dataclass(frozen=True)
class EnvVar
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Variable name |
| `value` | `str` | -- | Variable value |
| `prepend_path` | `bool` | `False` | If `True`, prepend value to existing `$name` |

### ActivationConfig

```
@dataclass(frozen=True)
class ActivationConfig
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `env_vars` | `tuple[EnvVar, ...]` | `()` | Environment variables to set |
| `path_prepends` | `tuple[str, ...]` | `()` | Directories to prepend to PATH |
| `app_name` | `str` | `""` | Used in comments and deactivation function name |
| `banner` | `str \| None` | `None` | Message to print on activation |

### ActivationScriptBuilder

```
class ActivationScriptBuilder
```

Generate shell-specific activation and deactivation scripts.

| Method | Returns | Description |
|--------|---------|-------------|
| `build(config, shell)` | `str` | Generate activation script |
| `build_deactivate(config, shell)` | `str` | Generate deactivation script |

**Supported shells:** bash, zsh, sh, dash, ksh (POSIX), fish, tcsh, PowerShell

Scripts save old variable values and restore them on deactivation.

---

## Tab Completion

### CompletionSpec

```
@dataclass(frozen=True)
class CompletionSpec
```

Full specification for generating shell completions.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `command` | `str` | -- | Top-level command name |
| `description` | `str` | `""` | Command description |
| `flags` | `tuple[CommandFlag, ...]` | `()` | Global flags |
| `subcommands` | `tuple[Subcommand, ...]` | `()` | Subcommands |

Supporting types: `CommandArg`, `CommandFlag`, `Subcommand` (each frozen dataclasses
with name, description, choices, and nesting support).

### CompletionGenerator

```
class CompletionGenerator
```

Generate tab-completion scripts from a command specification.

```python
def generate(self, spec: CompletionSpec, shell: ShellKind) -> str
```

**Supported shells:** bash, zsh, fish, PowerShell. Returns a comment for unsupported shells.

---

## Prompt Integration

### PromptHelper

```
class PromptHelper
```

Generate shell prompt integration snippets.

```python
def status_snippet(
    self,
    shell: ShellKind,
    env_var: str = "SNIFF_STATUS",
    format_str: str = "[{value}]",
) -> str
```

Returns shell-specific code that displays an environment variable value in the prompt
if it is set. Supports all shell families.

---

## Alias Suggestions

### AliasSuggestor

```
class AliasSuggestor
```

Suggest and render shell aliases for a CLI tool.

| Method | Returns | Description |
|--------|---------|-------------|
| `suggest(command, subcommands, common_flags)` | `list[AliasSuggestion]` | Generate alias suggestions |
| `render(suggestions, shell)` | `str` | Render as shell alias commands |

---

## Examples

### Detect shell

```python
from sniff.shell import ShellDetector

shell = ShellDetector().detect()
print(f"Shell: {shell.kind.value}")
print(f"Path: {shell.path}")
print(f"Config files: {shell.config_files}")
print(f"POSIX: {shell.is_posix}")
```

### Generate activation script

```python
from sniff.shell import (
    ShellDetector, ActivationScriptBuilder, ActivationConfig,
    EnvVar, ShellKind,
)

config = ActivationConfig(
    env_vars=(
        EnvVar(name="MLIR_DIR", value="/opt/llvm/lib/cmake/mlir"),
        EnvVar(name="LD_LIBRARY_PATH", value="/opt/llvm/lib", prepend_path=True),
    ),
    path_prepends=("/opt/llvm/bin",),
    app_name="apxm",
    banner="APXM environment activated",
)

shell = ShellDetector().detect()
builder = ActivationScriptBuilder()
script = builder.build(config, shell.kind)
print(script)
```

### Generate completions

```python
from sniff.shell import (
    CompletionGenerator, CompletionSpec, Subcommand,
    CommandFlag, ShellKind,
)

spec = CompletionSpec(
    command="apxm",
    description="APXM compiler toolkit",
    flags=(
        CommandFlag(long="--verbose", short="-v", description="Verbose output"),
    ),
    subcommands=(
        Subcommand(name="build", description="Build the project",
                   flags=(CommandFlag(long="--release", description="Release mode"),)),
        Subcommand(name="test", description="Run tests"),
        Subcommand(name="doctor", description="Check environment"),
    ),
)

gen = CompletionGenerator()
print(gen.generate(spec, ShellKind.BASH))
print(gen.generate(spec, ShellKind.FISH))
```

### Suggest aliases

```python
from sniff.shell import AliasSuggestor, ShellKind

suggestor = AliasSuggestor()
suggestions = suggestor.suggest(
    "apxm",
    subcommands=["build", "test", "doctor"],
    common_flags={"v": "--verbose"},
)

script = suggestor.render(suggestions, ShellKind.BASH)
print(script)
```
