"""Dependency checking - CLI tool existence and version validation."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class DependencySpec:
    """Specification for a dependency to check."""

    name: str  # Display name (e.g., "CMake")
    command: str  # Binary name (e.g., "cmake")
    version_arg: str = "--version"  # Flag to get version
    version_pattern: str | None = None  # Regex with capture group
    min_version: str | None = None  # Minimum version (e.g., "3.20")
    required: bool = True  # Is this required?
    fallback_commands: list[str] | None = None  # Alternative commands (e.g., ["conda"] for mamba)


@dataclass(frozen=True)
class DependencyResult:
    """Result of a dependency check."""

    name: str
    command: str
    found: bool
    version: str | None = None
    meets_minimum: bool = True
    required: bool = True
    error: str | None = None

    @property
    def ok(self) -> bool:
        """True if found and meets minimum version."""
        return self.found and self.meets_minimum


class DependencyChecker:
    """Check for tool dependencies and versions."""

    def __init__(self, timeout: float = 10.0):
        """
        Initialize dependency checker.

        Args:
            timeout: Seconds to wait for version commands.
        """
        self.timeout = timeout

    def check(self, spec: DependencySpec) -> DependencyResult:
        """
        Check if a dependency is available and meets version requirements.

        Args:
            spec: Dependency specification.

        Returns:
            DependencyResult with findings. Never raises.
        """
        # Try primary command
        path = shutil.which(spec.command)

        # Try fallbacks if primary not found
        if not path and spec.fallback_commands:
            for fallback in spec.fallback_commands:
                path = shutil.which(fallback)
                if path:
                    # Use fallback command for version check
                    actual_command = fallback
                    break
        else:
            actual_command = spec.command

        if not path:
            return DependencyResult(
                name=spec.name,
                command=spec.command,
                found=False,
                required=spec.required,
                error=f"{spec.command} not found in PATH",
            )

        # Get version
        version = self._get_version(actual_command, spec.version_arg, spec.version_pattern)

        # Check minimum version
        meets_minimum = True
        if version and spec.min_version:
            meets_minimum = self._compare_versions(version, spec.min_version)

        return DependencyResult(
            name=spec.name,
            command=spec.command,
            found=True,
            version=version,
            meets_minimum=meets_minimum,
            required=spec.required,
        )

    def _get_version(
        self, command: str, version_arg: str, version_pattern: str | None
    ) -> str | None:
        """Extract version from command output."""
        try:
            result = subprocess.run(
                [command, version_arg],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            output = result.stdout + result.stderr

            if version_pattern:
                match = re.search(version_pattern, output)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            else:
                # Try common patterns
                patterns = [
                    r"(\d+\.\d+\.\d+)",  # Semantic version
                    r"version\s+(\d+\.\d+)",  # "version X.Y"
                ]
                for pattern in patterns:
                    match = re.search(pattern, output, re.IGNORECASE)
                    if match:
                        return match.group(1)

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _compare_versions(self, version: str, minimum: str) -> bool:
        """Compare version strings (simple semantic version comparison)."""
        try:
            v_parts = [int(x) for x in version.split(".")[:3]]
            m_parts = [int(x) for x in minimum.split(".")[:3]]

            # Pad to 3 parts
            v_parts += [0] * (3 - len(v_parts))
            m_parts += [0] * (3 - len(m_parts))

            return tuple(v_parts) >= tuple(m_parts)
        except (ValueError, IndexError):
            # If parsing fails, assume it's OK
            return True
