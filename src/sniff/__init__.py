"""
sniff - Sniff out your Python development environment.

Like a packet sniffer for networks, sniff detects what's in your dev environment
through passive observation - no side effects, no changes, just answers.
"""

from sniff.detect import PlatformDetector, PlatformInfo
from sniff.deps import DependencyChecker, DependencySpec, DependencyResult
from sniff.conda import CondaDetector, CondaEnvironment
from sniff.tools import ToolChecker
from sniff.config import ConfigManager
from sniff.ci import CIDetector, CIInfo, CIProvider
from sniff.workspace import WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject

__version__ = "0.1.0"

__all__ = [
    "PlatformDetector",
    "PlatformInfo",
    "DependencyChecker",
    "DependencySpec",
    "DependencyResult",
    "CondaDetector",
    "CondaEnvironment",
    "ToolChecker",
    "ConfigManager",
    "CIDetector",
    "CIInfo",
    "CIProvider",
    "WorkspaceDetector",
    "WorkspaceInfo",
    "WorkspaceKind",
    "SubProject",
]
