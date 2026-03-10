"""Low-level tool detection utilities."""

from __future__ import annotations

import re
import shutil
import subprocess


class ToolChecker:
    """Low-level tool version extraction."""

    def __init__(self, timeout: float = 10.0):
        """
        Initialize tool checker.

        Args:
            timeout: Timeout for subprocess calls.
        """
        self.timeout = timeout

    def which(self, command: str) -> str | None:
        """
        Find command in PATH.

        Args:
            command: Command name to search for.

        Returns:
            Full path to command, or None if not found.
        """
        return shutil.which(command)

    def get_version(
        self, command: str, version_arg: str = "--version", pattern: str | None = None
    ) -> str | None:
        """
        Get version string from a command.

        Args:
            command: Command to run.
            version_arg: Argument to get version (default: "--version").
            pattern: Regex pattern to extract version. If None, uses common patterns.

        Returns:
            Version string if found, None otherwise.
        """
        try:
            result = subprocess.run(
                [command, version_arg],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            output = result.stdout + result.stderr

            if pattern:
                match = re.search(pattern, output)
                if match:
                    return match.group(1) if match.groups() else match.group(0)
            else:
                # Try common patterns
                patterns = [
                    r"(\d+\.\d+\.\d+)",  # Semantic version
                    r"version\s+(\d+\.\d+)",  # "version X.Y"
                ]
                for p in patterns:
                    match = re.search(p, output, re.IGNORECASE)
                    if match:
                        return match.group(1)

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None
