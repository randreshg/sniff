# sniff.version

Version constraint parsing, validation, and resolution.

**Module:** `sniff.version`
**Tier:** 2 (Extended Detection)
**Side effects:** None (pure data + logic)

Supports PEP 440-style and semver-style version specifications including exact,
comparison, compatible release, tilde, caret, wildcard, and range constraints.

---

## Classes

### Version

```
@total_ordering
@dataclass(frozen=True)
class Version
```

A parsed semantic version (`major.minor.patch[-pre][+build]`).
Comparison ignores build metadata per semver spec.
Pre-release versions sort before their release (`1.0.0-alpha < 1.0.0`).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `major` | `int` | -- | Major version |
| `minor` | `int` | `0` | Minor version |
| `patch` | `int` | `0` | Patch version |
| `pre` | `str \| None` | `None` | Pre-release identifier (e.g., `"beta.1"`) |
| `build` | `str \| None` | `None` | Build metadata (e.g., `"build42"`) |

#### Parsing

| Method | Returns | Description |
|--------|---------|-------------|
| `Version.parse(text)` | `Version` | Parse a version string. Accepts `"1"`, `"1.2"`, `"1.2.3"`, `"v1.2.3"`, `"1.2.3-beta.1"`, `"1.2.3+build42"`. Raises `ValueError` on failure. |
| `Version.try_parse(text)` | `Version \| None` | Like `parse()` but returns `None` instead of raising. |

#### Properties and Methods

| Name | Type | Description |
|------|------|-------------|
| `base` (property) | `Version` | Version without pre-release or build metadata |
| `bump_major()` | `Version` | Bump major, reset minor and patch |
| `bump_minor()` | `Version` | Bump minor, reset patch |
| `bump_patch()` | `Version` | Bump patch |

Supports comparison operators (`==`, `<`, `<=`, `>`, `>=`), hashing, and `str()`.

---

### ConstraintOp

```
enum ConstraintOp(enum.Enum)
```

| Value | Symbol | Description |
|-------|--------|-------------|
| `EQ` | `==` | Exact match |
| `NEQ` | `!=` | Not equal |
| `GTE` | `>=` | Greater or equal |
| `GT` | `>` | Greater than |
| `LTE` | `<=` | Less or equal |
| `LT` | `<` | Less than |
| `COMPAT` | `~=` | PEP 440 compatible release |
| `TILDE` | `~` | npm-style tilde |
| `CARET` | `^` | npm-style caret |

---

### VersionConstraint

```
@dataclass(frozen=True)
class VersionConstraint
```

A single version constraint like `>=1.80` or `^2.0.0`.

| Field | Type | Description |
|-------|------|-------------|
| `op` | `ConstraintOp` | Comparison operator |
| `version` | `Version` | Target version |

#### satisfied_by

```python
def satisfied_by(self, v: Version) -> bool
```

**Operator semantics:**

| Operator | Meaning |
|----------|---------|
| `~=X.Y` | `>=X.Y, <(X+1).0` |
| `~=X.Y.Z` | `>=X.Y.Z, <X.(Y+1).0` |
| `~X.Y.Z` | `>=X.Y.Z, <X.(Y+1).0` |
| `^X.Y.Z` (X>0) | `>=X.Y.Z, <(X+1).0.0` |
| `^0.Y.Z` (Y>0) | `>=0.Y.Z, <0.(Y+1).0` |
| `^0.0.Z` | `>=0.0.Z, <0.0.(Z+1)` |

---

### VersionSpec

```
@dataclass(frozen=True)
class VersionSpec
```

A version specification composed of one or more constraints. Supports
comma-separated constraints and wildcards.

| Field | Type | Description |
|-------|------|-------------|
| `constraints` | `tuple[VersionConstraint, ...]` | Individual constraints (conjunction) |
| `raw` | `str` | Original string |

#### Parsing

| Method | Returns | Description |
|--------|---------|-------------|
| `VersionSpec.parse(text)` | `VersionSpec` | Parse spec string. Raises `ValueError`. |
| `VersionSpec.try_parse(text)` | `VersionSpec \| None` | Like `parse()` but returns `None`. |

**Accepted formats:** `">=1.80"`, `"~=3.11"`, `"^2.0.0"`, `">=1.0,<2.0"`, `"1.2.*"`, `"==1.0.0"`

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `satisfied_by(version)` | `bool` | Check if a version satisfies all constraints. Accepts `str` or `Version`. |
| `best_match(candidates)` | `Version \| None` | Find highest satisfying version from a list. |

---

## Utility Functions

### compare_versions

```python
def compare_versions(a: str, b: str) -> int
```

Compare two version strings. Returns `-1` if `a < b`, `0` if equal, `1` if `a > b`.
Raises `ValueError` if either string cannot be parsed.

### version_satisfies

```python
def version_satisfies(version: str, spec: str) -> bool
```

Convenience function. Returns `True` if satisfied, `False` if not or if parsing fails.

---

## Examples

### Parse and compare versions

```python
from sniff.version import Version

v1 = Version.parse("1.80.0")
v2 = Version.parse("2.0.0-beta.1")

print(v1 < v2)    # True
print(v2.pre)     # "beta.1"
print(v2.base)    # Version(2.0.0)
```

### Check version constraints

```python
from sniff.version import VersionSpec, version_satisfies

spec = VersionSpec.parse(">=1.80,<2.0")
print(spec.satisfied_by("1.85.0"))  # True
print(spec.satisfied_by("2.0.0"))   # False

# Convenience function
print(version_satisfies("3.12.0", "~=3.11"))  # True (>=3.11, <4.0)
print(version_satisfies("1.2.3", "^1.0.0"))   # True (>=1.0.0, <2.0.0)
```

### Find best version match

```python
from sniff.version import VersionSpec

spec = VersionSpec.parse(">=1.70,<2.0")
candidates = ["1.65.0", "1.80.0", "1.82.0", "2.0.0", "2.1.0"]
best = spec.best_match(candidates)
print(best)  # Version(1.82.0)
```

### Wildcard constraints

```python
from sniff.version import VersionSpec

spec = VersionSpec.parse("1.2.*")
print(spec.satisfied_by("1.2.0"))  # True
print(spec.satisfied_by("1.2.9"))  # True
print(spec.satisfied_by("1.3.0"))  # False
```
