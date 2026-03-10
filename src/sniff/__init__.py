"""
sniff - Sniff out your Python development environment.

Like a packet sniffer for networks, sniff detects what's in your dev environment
through passive observation - no side effects, no changes, just answers.
"""

from sniff.detect import PlatformDetector, PlatformInfo
from sniff.deps import DependencyChecker, DependencySpec, DependencyResult
from sniff.conda import COMMON_INSTALL_PATHS, CondaDetector, CondaEnvironment, CondaValidation
from sniff.tools import ToolChecker
from sniff.config import ConfigManager
from sniff.ci import CIDetector, CIInfo, CIProvider
from sniff.ci_build import CIBuildAdvisor, CIBuildHints
from sniff.workspace import WorkspaceDetector, WorkspaceInfo, WorkspaceKind, SubProject
from sniff.version import Version, VersionSpec, VersionConstraint, compare_versions, version_satisfies
from sniff.version_managers import VersionManagerDetector, VersionManagerInfo, ManagedVersion
from sniff.lockfile import LockfileParser, LockfileInfo, LockfileKind, LockedDependency
from sniff.compiler import CompilerDetector, CompilerFamily, CompilerInfo, ToolchainInfo
from sniff.build import BuildSystemDetector, BuildSystemInfo, BuildSystem, BuildTarget
from sniff.cache import BuildCacheDetector, BuildCacheInfo, CacheKind
from sniff.paths import PathManager, PathCategory, ResolvedPath, ToolPath, LibraryPath, ProjectPaths
from sniff.shell import (
    ShellDetector,
    ShellInfo,
    ShellKind,
    ActivationScriptBuilder,
    ActivationConfig,
    EnvVar,
    CompletionGenerator,
    CompletionSpec,
    PromptHelper,
    AliasSuggestor,
)
from sniff.toolchain import (
    ToolchainProfile,
    EnvVarBuilder,
    CMakeToolchain,
    CondaToolchain,
)
from sniff.env import EnvSnapshot
from sniff.diagnostic import (
    DiagnosticReport,
    DiagnosticCheck,
    CheckRegistry,
    DiagnosticRunner,
    TextFormatter,
    JsonFormatter,
    MarkdownFormatter,
)
from sniff.diagnostic_checks import PlatformCheck, DependencyCheck, CIEnvironmentCheck
from sniff.libpath import LibraryPathInfo, LibraryPathResolver
from sniff.commands import (
    CommandStatus,
    CommandMeta,
    CommandProvider,
    CommandRegistry,
    command,
)
from sniff.validate import ValidationReport, EnvironmentValidator
from sniff.remediate import (
    IssueSeverity,
    FixStatus,
    DetectedIssue,
    FixResult,
    Remediator,
    RemediatorRegistry,
)
from sniff.scaffold import (
    ProjectLanguage,
    ProjectFramework,
    ProjectType,
    ProjectTypeDetector,
    FileTemplate,
    TemplateSet,
    TemplateRegistry,
    SetupStep,
    SetupScript,
    SetupScriptBuilder,
)

__version__ = "2.0.0"

__all__ = [
    "PlatformDetector",
    "PlatformInfo",
    "DependencyChecker",
    "DependencySpec",
    "DependencyResult",
    "COMMON_INSTALL_PATHS",
    "CondaDetector",
    "CondaEnvironment",
    "CondaValidation",
    "ToolChecker",
    "ConfigManager",
    "CIDetector",
    "CIInfo",
    "CIProvider",
    "CIBuildAdvisor",
    "CIBuildHints",
    "WorkspaceDetector",
    "WorkspaceInfo",
    "WorkspaceKind",
    "SubProject",
    "Version",
    "VersionSpec",
    "VersionConstraint",
    "compare_versions",
    "version_satisfies",
    "VersionManagerDetector",
    "VersionManagerInfo",
    "ManagedVersion",
    "LockfileParser",
    "LockfileInfo",
    "LockfileKind",
    "LockedDependency",
    "CompilerDetector",
    "CompilerFamily",
    "CompilerInfo",
    "ToolchainInfo",
    "BuildSystemDetector",
    "BuildSystemInfo",
    "BuildSystem",
    "BuildTarget",
    "BuildCacheDetector",
    "BuildCacheInfo",
    "CacheKind",
    "ShellDetector",
    "ShellInfo",
    "ShellKind",
    "ActivationScriptBuilder",
    "ActivationConfig",
    "EnvVar",
    "CompletionGenerator",
    "CompletionSpec",
    "PromptHelper",
    "AliasSuggestor",
    "PathManager",
    "PathCategory",
    "ResolvedPath",
    "ToolPath",
    "LibraryPath",
    "ProjectPaths",
    "ToolchainProfile",
    "EnvVarBuilder",
    "CMakeToolchain",
    "CondaToolchain",
    "EnvSnapshot",
    "ProjectLanguage",
    "ProjectFramework",
    "ProjectType",
    "ProjectTypeDetector",
    "FileTemplate",
    "TemplateSet",
    "TemplateRegistry",
    "SetupStep",
    "SetupScript",
    "SetupScriptBuilder",
    # diagnostic
    "DiagnosticReport",
    "DiagnosticCheck",
    "CheckRegistry",
    "DiagnosticRunner",
    "TextFormatter",
    "JsonFormatter",
    "MarkdownFormatter",
    # diagnostic_checks
    "PlatformCheck",
    "DependencyCheck",
    "CIEnvironmentCheck",
    # libpath
    "LibraryPathInfo",
    "LibraryPathResolver",
    # commands
    "CommandStatus",
    "CommandMeta",
    "CommandProvider",
    "CommandRegistry",
    "command",
    # validate
    "ValidationReport",
    "EnvironmentValidator",
    # remediate
    "IssueSeverity",
    "FixStatus",
    "DetectedIssue",
    "FixResult",
    "Remediator",
    "RemediatorRegistry",
]
