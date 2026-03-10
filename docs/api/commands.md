# sniff.commands

Command/plugin registry for project CLI tooling.

**Module:** `sniff.commands`
**Tier:** 3 (Frameworks)
**Side effects:** None (the registry stores and queries metadata; it never executes commands)

Passive command registry that allows projects to register commands with rich metadata
(name, group, help, dependencies), discover available commands, declare prerequisites
and lifecycle hooks, and generate help/documentation.

---

## Classes

### CommandStatus

```
enum CommandStatus(enum.Enum)
```

| Value | Description |
|-------|-------------|
| `AVAILABLE` | Command is available for use |
| `DISABLED` | Command is temporarily disabled |
| `DEPRECATED` | Command is deprecated |

---

### CommandMeta

```
@dataclass(frozen=True)
class CommandMeta
```

Metadata for a registered command. Immutable descriptor that holds everything a CLI
framework needs to wire up a command without importing the implementation module.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Command name |
| `group` | `str` | `""` | Group name (for subcommand grouping) |
| `help` | `str` | `""` | Help text |
| `hidden` | `bool` | `False` | Whether to hide from help listings |
| `status` | `CommandStatus` | `AVAILABLE` | Lifecycle status |
| `requires` | `tuple[str, ...]` | `()` | Names of other commands that must exist |
| `setup` | `Callable \| None` | `None` | Setup lifecycle callable |
| `execute` | `Callable \| None` | `None` | Execute lifecycle callable |
| `teardown` | `Callable \| None` | `None` | Teardown lifecycle callable |
| `tags` | `dict[str, str]` | `{}` | Arbitrary key-value metadata |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `qualified_name` | `str` | Group-qualified name (e.g., `"build:compiler"`) |
| `is_available` | `bool` | `True` if status is `AVAILABLE` |
| `has_lifecycle` | `bool` | `True` if any lifecycle callable is set |

---

## Protocols

### CommandProvider

```
@runtime_checkable
class CommandProvider(Protocol)
```

Protocol for objects that supply commands to a registry.

| Method | Returns | Description |
|--------|---------|-------------|
| `commands()` | `Sequence[CommandMeta]` | The commands this provider offers |

---

## Classes (continued)

### CommandRegistry

```
class CommandRegistry
```

Passive command registry. Stores `CommandMeta` descriptors and exposes
query/discovery helpers. Never executes anything.

#### Registration

| Method | Description |
|--------|-------------|
| `register(meta)` | Register a command. Raises `ValueError` if name already exists. |
| `register_all(metas)` | Register multiple commands |
| `register_provider(provider)` | Register all commands from a `CommandProvider` |
| `unregister(qualified_name)` | Remove a command. Returns removed meta or `None`. |

#### Queries

| Method | Returns | Description |
|--------|---------|-------------|
| `get(qualified_name)` | `CommandMeta \| None` | Look up by qualified name |
| `all(*, include_hidden=False)` | `list[CommandMeta]` | All commands, sorted |
| `by_group(group)` | `list[CommandMeta]` | Commands in a specific group |
| `groups()` | `list[str]` | Distinct group names, sorted |
| `by_status(status)` | `list[CommandMeta]` | Commands with a given status |
| `by_tag(key, value=None)` | `list[CommandMeta]` | Commands matching a tag |
| `names` (property) | `list[str]` | All qualified names, sorted |

Also supports `in`, `len()`, and iteration.

#### Dependency Queries

| Method | Returns | Description |
|--------|---------|-------------|
| `missing_requirements(name)` | `list[str]` | Unresolved requirement names |
| `dependents(name)` | `list[CommandMeta]` | Commands that require this one |
| `resolve_order(name)` | `list[str] \| None` | Topological order to satisfy all transitive requirements. `None` if cycle detected. |

#### Help

| Method | Returns | Description |
|--------|---------|-------------|
| `help_text(name)` | `str \| None` | Formatted help for a single command |
| `help_summary(*, include_hidden=False)` | `str` | Summary of all commands, grouped |

---

## Decorator

### @command

```python
@command(registry, name=None, *, group="", help="", requires=(), hidden=False, tags=None)
```

Decorator that registers a function as a command. The decorated function becomes the
`execute` callable on the `CommandMeta`. The function itself is returned unchanged.

---

## Examples

### Register commands manually

```python
from sniff.commands import CommandRegistry, CommandMeta

registry = CommandRegistry()

registry.register(CommandMeta(
    name="build",
    group="dev",
    help="Build the project",
))

registry.register(CommandMeta(
    name="test",
    group="dev",
    help="Run test suite",
    requires=("dev:build",),
))

# Query
build = registry.get("dev:build")
print(registry.help_summary())
```

### Use the @command decorator

```python
from sniff.commands import CommandRegistry, command

registry = CommandRegistry()

@command(registry, group="build", help="Compile the project")
def compile(release: bool = True):
    ...

@command(registry, group="build", help="Run linter", requires=("build:compile",))
def lint():
    ...

# Check dependency resolution
order = registry.resolve_order("build:lint")
# ["build:compile", "build:lint"]
```

### Implement a CommandProvider

```python
from sniff.commands import CommandRegistry, CommandMeta, CommandProvider

class BuildCommandProvider:
    def commands(self):
        return [
            CommandMeta(name="build", group="cargo", help="cargo build"),
            CommandMeta(name="test", group="cargo", help="cargo test"),
            CommandMeta(name="clippy", group="cargo", help="cargo clippy"),
        ]

registry = CommandRegistry()
registry.register_provider(BuildCommandProvider())

for cmd in registry.by_group("cargo"):
    print(f"  {cmd.name}: {cmd.help}")
```

### Filter by tags

```python
from sniff.commands import CommandRegistry, CommandMeta

registry = CommandRegistry()
registry.register(CommandMeta(
    name="build", help="Build project",
    tags={"lang": "rust", "ci": "true"},
))
registry.register(CommandMeta(
    name="docs", help="Generate docs",
    tags={"lang": "rust", "ci": "false"},
))

ci_commands = registry.by_tag("ci", "true")
rust_commands = registry.by_tag("lang", "rust")
```
