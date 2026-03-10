"""Conda environment detection."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CondaEnvironment:
    """Conda environment information."""

    name: str
    prefix: Path
    is_active: bool = False
    python_version: str | None = None


class CondaDetector:
    """Detect conda/mamba environments."""

    def __init__(self, timeout: float = 10.0):
        """
        Initialize conda detector.

        Args:
            timeout: Timeout for conda commands.
        """
        self.timeout = timeout

    def find_active(self) -> CondaEnvironment | None:
        """
        Find the currently active conda environment.

        Returns:
            CondaEnvironment if one is active, None otherwise.
        """
        conda_prefix = os.environ.get("CONDA_PREFIX")
        conda_name = os.environ.get("CONDA_DEFAULT_ENV")

        if not conda_prefix:
            return None

        prefix = Path(conda_prefix)
        name = conda_name or prefix.name

        # Try to get Python version
        python_version = self._get_python_version(prefix)

        return CondaEnvironment(
            name=name, prefix=prefix, is_active=True, python_version=python_version
        )

    def find_environment(self, name: str) -> CondaEnvironment | None:
        """
        Find a conda environment by name.

        Args:
            name: Environment name to search for.

        Returns:
            CondaEnvironment if found, None otherwise.
        """
        # Check if conda is available
        import shutil

        conda_cmd = shutil.which("conda") or shutil.which("mamba")
        if not conda_cmd:
            return None

        try:
            # Get list of environments
            result = subprocess.run(
                [conda_cmd, "env", "list", "--json"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            envs = data.get("envs", [])

            # Find matching environment
            for env_path in envs:
                env_path = Path(env_path)
                if env_path.name == name:
                    # Check if this is the active environment
                    active_prefix = os.environ.get("CONDA_PREFIX")
                    is_active = str(env_path) == active_prefix

                    python_version = self._get_python_version(env_path)

                    return CondaEnvironment(
                        name=name,
                        prefix=env_path,
                        is_active=is_active,
                        python_version=python_version,
                    )

            return None

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            return None

    def _get_python_version(self, prefix: Path) -> str | None:
        """Get Python version in a conda environment."""
        # Try to find python executable
        if os.name == "nt":  # Windows
            python_path = prefix / "python.exe"
        else:  # Unix
            python_path = prefix / "bin" / "python"

        if not python_path.exists():
            return None

        try:
            result = subprocess.run(
                [str(python_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )

            output = result.stdout + result.stderr
            # Parse "Python X.Y.Z"
            import re

            match = re.search(r"Python\s+(\d+\.\d+\.\d+)", output)
            if match:
                return match.group(1)

            return None

        except (subprocess.TimeoutExpired, OSError):
            return None
