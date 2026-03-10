# sniff.scaffold

Project scaffolding -- detect project type, provide templates, generate setup scripts.

**Module:** `sniff.scaffold`
**Tier:** 3 (Frameworks)
**Side effects:** None (detection is pure, template/script generation produces strings)

Composes existing detectors to determine the project type and provide appropriate
scaffolding support including file templates and setup script generation.

---

## Enums

### ProjectLanguage

```
enum ProjectLanguage(enum.Enum)
```

Primary programming language of a project.

`PYTHON`, `RUST`, `JAVASCRIPT`, `TYPESCRIPT`, `GO`, `JAVA`, `CSHARP`, `CPP`, `C`,
`RUBY`, `PHP`, `SWIFT`, `KOTLIN`, `SCALA`, `UNKNOWN`

### ProjectFramework

```
enum ProjectFramework(enum.Enum)
```

Detected framework or build system.

**Python:** `DJANGO`, `FLASK`, `FASTAPI`, `SETUPTOOLS`, `HATCH`, `POETRY`, `PDM`, `FLIT`, `MATURIN`
**JavaScript/TypeScript:** `REACT`, `NEXT`, `VUE`, `NUXT`, `ANGULAR`, `SVELTE`, `EXPRESS`, `VITE`
**Rust:** `CARGO`, `WASM_PACK`
**Go:** `GO_MODULE`
**Java/JVM:** `MAVEN`, `GRADLE`, `SBT`
**C/C++:** `CMAKE`, `MESON`, `MAKE`, `AUTOTOOLS`
**Ruby:** `RAILS`, `BUNDLER`
**Generic:** `NONE`

---

## Data Classes

### ProjectType

```
@dataclass(frozen=True)
class ProjectType
```

Detected project type combining language, framework, and metadata.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | `ProjectLanguage` | -- | Primary language |
| `framework` | `ProjectFramework` | `NONE` | Detected framework |
| `is_library` | `bool` | `False` | Heuristic: is a library |
| `is_application` | `bool` | `False` | Heuristic: is an application |
| `is_monorepo` | `bool` | `False` | Monorepo/workspace detected |
| `has_tests` | `bool` | `False` | Test directory/files found |
| `has_ci` | `bool` | `False` | CI configuration found |
| `has_docs` | `bool` | `False` | Documentation directory found |
| `entry_points` | `tuple[str, ...]` | `()` | Detected entry point files |

### FileTemplate

```
@dataclass(frozen=True)
class FileTemplate
```

A template for a single file to scaffold.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `relative_path` | `str` | -- | Relative file path |
| `content` | `str` | -- | File content |
| `executable` | `bool` | `False` | Whether the file should be executable |
| `description` | `str` | `""` | Description |

### TemplateSet

```
@dataclass(frozen=True)
class TemplateSet
```

A named collection of file templates.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Template set name |
| `description` | `str` | -- | Description |
| `language` | `ProjectLanguage` | -- | Target language |
| `framework` | `ProjectFramework` | `NONE` | Target framework |
| `files` | `tuple[FileTemplate, ...]` | `()` | Files in this set |
| `tags` | `tuple[str, ...]` | `()` | Tags for searching |

**Properties:** `file_count`, `paths`

### SetupStep / SetupScript

```
@dataclass(frozen=True)
class SetupStep
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Step name |
| `command` | `str` | -- | Shell command |
| `description` | `str` | `""` | Description |
| `condition` | `str \| None` | `None` | Shell condition to check first |
| `optional` | `bool` | `False` | Whether failure is non-fatal |
| `working_dir` | `str \| None` | `None` | Relative working directory |

```
@dataclass(frozen=True)
class SetupScript
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | -- | Script name |
| `description` | `str` | -- | Description |
| `steps` | `tuple[SetupStep, ...]` | `()` | Ordered setup steps |
| `env_vars` | `tuple[tuple[str, str], ...]` | `()` | Environment variables |

**Properties:** `step_count`, `required_steps`, `optional_steps`

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `render(shell="bash")` | `str` | Render as shell script. Supports `"bash"`, `"fish"`, `"powershell"`. |

---

## Detector

### ProjectTypeDetector

```
class ProjectTypeDetector
```

Detect the type of project in a directory. Pure detection -- no subprocess calls.

#### detect

```python
def detect(self, root: Path | None = None) -> ProjectType
```

Detect project type at the given root. Always returns a valid `ProjectType`
(with `UNKNOWN` language if detection fails).

**Detection markers (in priority order):**

| Marker File | Language | Framework |
|-------------|----------|-----------|
| `pyproject.toml` | Python | (refined by build backend and dependencies) |
| `setup.py` / `setup.cfg` | Python | Setuptools |
| `Cargo.toml` | Rust | Cargo |
| `package.json` | JavaScript | (refined by dependencies) |
| `tsconfig.json` | TypeScript | (refined by dependencies) |
| `go.mod` | Go | Go Module |
| `pom.xml` | Java | Maven |
| `build.gradle(.kts)` | Java | Gradle |
| `CMakeLists.txt` | C++ | CMake |
| `meson.build` | C++ | Meson |
| `Makefile` | C | Make |
| `Gemfile` | Ruby | Bundler |

---

## Protocols

### TemplateProvider

```
class TemplateProvider(Protocol)
```

Protocol for objects that provide template sets.

| Method | Returns | Description |
|--------|---------|-------------|
| `get_templates(language, framework=NONE)` | `list[TemplateSet]` | Templates matching criteria |

---

## Registries and Builders

### TemplateRegistry

| Method | Description |
|--------|-------------|
| `register_provider(provider)` | Register a `TemplateProvider` |
| `register_template_set(ts)` | Register a standalone `TemplateSet` |
| `find(language, framework=NONE)` | Find matching template sets |
| `find_by_tag(tag)` | Find template sets by tag |
| `all_templates` (property) | All registered template sets |

### SetupScriptBuilder

| Method | Returns | Description |
|--------|---------|-------------|
| `build(project_type)` | `SetupScript` | Generate setup script for project type |
| `build_with_platform(project_type, os_name, pkg_manager)` | `SetupScript` | Platform-aware setup with system dependency installation |

---

## Examples

### Detect project type

```python
from sniff.scaffold import ProjectTypeDetector

detector = ProjectTypeDetector()
project = detector.detect()

print(f"Language: {project.language.value}")
print(f"Framework: {project.framework.value}")
print(f"Library: {project.is_library}, App: {project.is_application}")
print(f"Monorepo: {project.is_monorepo}")
print(f"Entry points: {project.entry_points}")
```

### Generate setup script

```python
from sniff.scaffold import ProjectTypeDetector, SetupScriptBuilder

project = ProjectTypeDetector().detect()
script = SetupScriptBuilder().build(project)

print(script.render("bash"))
```

### Platform-aware setup

```python
from sniff.scaffold import ProjectTypeDetector, SetupScriptBuilder
from sniff import PlatformDetector

project = ProjectTypeDetector().detect()
platform = PlatformDetector().detect()

script = SetupScriptBuilder().build_with_platform(
    project,
    os_name=platform.os,
    pkg_manager=platform.pkg_manager,
)
print(script.render("bash"))
```

### Register custom templates

```python
from sniff.scaffold import TemplateRegistry, TemplateSet, FileTemplate, ProjectLanguage

registry = TemplateRegistry()
registry.register_template_set(TemplateSet(
    name="python-cli",
    description="Python CLI application starter",
    language=ProjectLanguage.PYTHON,
    tags=("cli", "starter"),
    files=(
        FileTemplate(
            relative_path="src/myapp/__init__.py",
            content='"""My application."""\n',
        ),
        FileTemplate(
            relative_path="src/myapp/__main__.py",
            content='from myapp.cli import main\nmain()\n',
        ),
    ),
))

results = registry.find(ProjectLanguage.PYTHON)
```
