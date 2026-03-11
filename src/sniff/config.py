"""Configuration management with TOML and layered precedence."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    # Fallback for Python 3.10
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


class ConfigManager:
    """
    Configuration manager with layered precedence.

    Precedence (highest to lowest):
    1. Environment variables (APP_SECTION_KEY)
    2. Project config (.app/config.toml)
    3. User config (~/.config/app/config.toml)
    4. System config (/etc/app/config.toml) - Linux/macOS only
    5. Built-in defaults
    """

    def __init__(
        self,
        app_name: str,
        config_dir: str | None = None,
        env_prefix: str | None = None,
        defaults: dict[str, Any] | None = None,
    ):
        """
        Initialize configuration manager.

        Args:
            app_name: Application name (e.g., "myapp").
            config_dir: Config directory name (e.g., ".myapp"). Defaults to app_name.
            env_prefix: Environment variable prefix. Defaults to app_name.upper().
            defaults: Built-in default values.
        """
        self.app_name = app_name
        self.config_dir = config_dir or f".{app_name}"
        self.env_prefix = env_prefix or app_name.upper()
        self.defaults = defaults or {}
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from all sources."""
        # Start with defaults
        self._config = self.defaults.copy()

        # Load system config (Linux/macOS only)
        if os.name != "nt":
            system_config = Path(f"/etc/{self.app_name}/config.toml")
            if system_config.exists():
                self._merge(self._load_toml(system_config))

        # Load user config
        user_config = Path.home() / ".config" / self.app_name / "config.toml"
        if user_config.exists():
            self._merge(self._load_toml(user_config))

        # Load project config (walk up from cwd)
        project_config = self._find_project_config()
        if project_config and project_config.exists():
            self._merge(self._load_toml(project_config))

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _load_toml(self, path: Path) -> dict[str, Any]:
        """Load TOML file."""
        if tomllib is None:
            return {}

        try:
            with open(path, "rb") as f:
                return tomllib.load(f)
        except (OSError, ValueError):
            return {}

    def _find_project_config(self) -> Path | None:
        """Find project config by walking up from cwd."""
        current = Path.cwd()
        while current != current.parent:
            config_path = current / self.config_dir / "config.toml"
            if config_path.exists():
                return config_path
            current = current.parent
        return None

    def _merge(self, source: dict[str, Any]) -> None:
        """Deep merge source into config."""
        for key, value in source.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._deep_merge(self._config[key], value)
            else:
                self._config[key] = value

    def _deep_merge(self, target: dict[str, Any], source: dict[str, Any]) -> None:
        """Recursively merge source into target."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        prefix = f"{self.env_prefix}_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert ENV_SECTION_KEY to section.key
                config_key = key[len(prefix):].lower().replace("_", ".")
                self.set(config_key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "database.path").
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.

        Args:
            key: Configuration key (e.g., "database.path").
            value: Value to set.
        """
        parts = key.split(".")
        target = self._config

        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value

    def to_dict(self) -> dict[str, Any]:
        """Get full configuration as dictionary."""
        return self._config.copy()


# ---------------------------------------------------------------------------
# ConfigSource -- frozen record of a single config value origin
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConfigSource:
    """Where a config value came from."""

    key: str
    value: Any
    source: str  # "environment" | "file" | "default" | "cli"
    file_path: Path | None  # If from file
    line_number: int | None  # If from file
    precedence: int  # Higher = more important


# ---------------------------------------------------------------------------
# ConfigReconciler -- multi-source config debugging
# ---------------------------------------------------------------------------

class ConfigReconciler:
    """Reconcile configuration from multiple sources.

    Helps debug "why is this value X?" questions by tracking every source
    that provides a value for a given key and resolving via precedence.
    """

    def __init__(self) -> None:
        self.sources: dict[str, list[ConfigSource]] = {}

    def add_source(self, source: ConfigSource) -> None:
        """Add a configuration source."""
        if source.key not in self.sources:
            self.sources[source.key] = []
        self.sources[source.key].append(source)

    def resolve(self, key: str) -> ConfigSource | None:
        """Resolve final value (highest precedence wins)."""
        if key not in self.sources:
            return None
        return max(self.sources[key], key=lambda s: s.precedence)

    def explain(self, key: str) -> str:
        """Explain how a value was resolved."""
        if key not in self.sources:
            return f"{key}: not found"

        sources = sorted(self.sources[key], key=lambda s: s.precedence)
        lines = [f"Configuration for '{key}':"]
        for source in sources:
            if source.source == "file" and source.file_path:
                lines.append(
                    f"  {source.source}: {source.value} "
                    f"(from {source.file_path}:{source.line_number})"
                )
            else:
                lines.append(f"  {source.source}: {source.value}")

        final = self.resolve(key)
        lines.append(f"  → Final value: {final.value} (from {final.source})")
        return "\n".join(lines)

    def keys(self) -> list[str]:
        """Return all tracked configuration keys."""
        return sorted(self.sources.keys())

    def all_sources(self, key: str) -> list[ConfigSource]:
        """Return all sources for a key, sorted by precedence (ascending)."""
        if key not in self.sources:
            return []
        return sorted(self.sources[key], key=lambda s: s.precedence)
