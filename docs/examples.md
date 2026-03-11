# sniff 2.1 Examples

Complete working examples demonstrating sniff 2.1.0 features in real-world patterns.

---

## Table of Contents

- [Environment Snapshot and Comparison](#environment-snapshot-and-comparison)
- [APXM CLI Application](#apxm-cli-application)
- [Tully Experiment Tracking](#tully-experiment-tracking)
- [SBOM Generation for Compliance](#sbom-generation-for-compliance)
- [Config Debugging](#config-debugging)
- [CI/CD Environment Report](#cicd-environment-report)
- [Reproducibility Guard](#reproducibility-guard)

---

## Environment Snapshot and Comparison

Capture, save, and compare execution environments.

```python
"""environment_guard.py -- Compare environments between runs."""
import json
from pathlib import Path
from sniff.context import ExecutionContext


def save_environment(path: str = "environment.json"):
    """Capture and save the current environment."""
    ctx = ExecutionContext.capture()
    with open(path, "w") as f:
        json.dump(ctx.to_dict(), f, indent=2)
    print(f"Environment saved to {path}")
    print(f"Fingerprint: {ctx.fingerprint()}")


def compare_environment(baseline: str = "environment.json"):
    """Compare current environment against a saved baseline."""
    with open(baseline) as f:
        old_ctx = ExecutionContext.from_dict(json.load(f))

    current = ExecutionContext.capture()
    diff = current.diff(old_ctx)

    if diff.is_compatible():
        print("Environments are compatible")
    else:
        print("WARNING: environments differ")
        print(diff.summary())
        return False
    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "save":
        save_environment()
    else:
        compare_environment()
```

---

## APXM CLI Application

Full APXM CLI using `sniff.Typer` with built-in commands.

```python
"""apxm_cli.py -- APXM compiler CLI with sniff integration."""
from pathlib import Path
from sniff import Typer

# Assume apxm.__version__ exists
__version__ = "0.2.0"

app = Typer(
    name="apxm",
    help="APXM CLI - Compiler and runtime driver",
    add_doctor_command=True,
    add_version_command=True,
    add_env_command=True,
    project_version=__version__,
)

# Session hooks for logging
@app.before_command
def log_environment(ctx):
    """Log environment state before each command."""
    if ctx and ctx.ci_info and hasattr(ctx.ci_info, 'is_ci') and ctx.ci_info.is_ci:
        print(f"[CI] Running on {ctx.ci_info.provider}")


@app.command()
def build(
    target: str,
    opt_level: int = 2,
    debug: bool = False,
):
    """Build APXM compiler for the given target."""
    print(f"Building target: {target}")
    print(f"Platform: {app.platform.os} {app.platform.arch}")
    print(f"Optimization: O{opt_level}")

    if app.conda_env:
        print(f"Conda environment: {app.conda_env.name}")

    if debug:
        print(f"CPU: {app.context.cpu_info.model}")
        print(f"Memory: {app.context.memory_info.total_mb} MB")


@app.command()
def compile(
    input_file: str,
    output: str = "out.apxmobj",
    pipeline: str = "default",
):
    """Compile an ApxmGraph JSON to .apxmobj artifact."""
    print(f"Compiling {input_file} -> {output}")
    print(f"Pipeline: {pipeline}")

    # Access workspace for git info
    git = app.workspace.git_info
    if git:
        print(f"Git: {git.branch}@{git.commit_sha[:8]}")
        if git.is_dirty:
            print("WARNING: working tree has uncommitted changes")


@app.command()
def run(artifact: str, backend: str = "local"):
    """Execute a compiled .apxmobj artifact."""
    print(f"Running {artifact} on {backend} backend")

    gpus = app.context.gpu_info
    if gpus:
        for gpu in gpus:
            print(f"  GPU: {gpu.vendor} {gpu.model} ({gpu.memory_mb} MB)")
    else:
        print("  No GPUs detected, running on CPU")


if __name__ == "__main__":
    app()
```

Usage:
```bash
$ apxm doctor
$ apxm version-cmd
$ apxm build lib --opt-level 3 --debug
$ apxm compile graph.json --output model.apxmobj
$ apxm run model.apxmobj --backend cuda
```

---

## Tully Experiment Tracking

Automatic experiment tracking with `sniff.Typer`.

```python
"""tully_cli.py -- Experiment tracking with automatic environment capture."""
from pathlib import Path
from sniff import Typer

app = Typer(
    name="tully",
    help="Tully experiment tracker",
    enable_tracking=True,
    tully_db_path=Path("experiments.db"),
    tully_experiment_name="training-runs",
    add_doctor_command=True,
    add_version_command=True,
    project_version="0.1.0",
)


@app.command(track=True)
def train(
    epochs: int = 10,
    lr: float = 0.001,
    batch_size: int = 32,
):
    """Train a model with automatic tracking.

    Environment is captured automatically.
    Metrics and artifacts are logged to Tully.
    Success/failure is recorded on exit.
    """
    for epoch in range(epochs):
        # Simulate training
        loss = 1.0 / (epoch + 1)
        accuracy = 1.0 - loss

        app.log_metric("loss", loss, step=epoch)
        app.log_metric("accuracy", accuracy, step=epoch)
        print(f"Epoch {epoch}: loss={loss:.4f}, acc={accuracy:.4f}")

    # Log model artifact
    model_path = Path("output/model.pt")
    if model_path.exists():
        app.log_artifact("model", model_path)


@app.command(track=False)
def list_runs():
    """List experiment runs (not tracked)."""
    print("Listing runs...")


if __name__ == "__main__":
    app()
```

---

## SBOM Generation for Compliance

Generate Software Bill of Materials for auditing.

```python
"""sbom_export.py -- Generate SBOM in SPDX and CycloneDX formats."""
from pathlib import Path
from sniff.manifest import EnvironmentManifest


def generate_sbom(output_dir: str = "."):
    """Generate SBOM files for the current environment."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Generate manifest
    manifest = EnvironmentManifest.generate(
        tool_name="my-project",
        include_system=True,
        include_conda=True,
    )

    # Export SPDX
    spdx_path = out / "sbom.spdx"
    spdx_path.write_text(manifest.to_spdx())
    print(f"SPDX manifest: {spdx_path}")

    # Export CycloneDX JSON
    cdx_path = out / "sbom.cdx.json"
    cdx_path.write_text(manifest.to_cyclonedx())
    print(f"CycloneDX manifest: {cdx_path}")

    # Summary
    print(f"\nPackages detected:")
    print(f"  Python: {len(manifest.python_packages)}")
    print(f"  Conda:  {len(manifest.conda_packages)}")
    print(f"  System: {len(manifest.system_packages)}")

    # List Python packages with licenses
    print(f"\nPython packages:")
    for pkg in manifest.python_packages[:10]:
        license_str = pkg.license or "Unknown"
        print(f"  {pkg.name} {pkg.version} ({license_str})")
    if len(manifest.python_packages) > 10:
        print(f"  ... and {len(manifest.python_packages) - 10} more")


def verify_checksums():
    """Verify file integrity against a manifest."""
    manifest = EnvironmentManifest.generate(
        checksum_paths=[
            Path("pyproject.toml"),
            Path("src/sniff/__init__.py"),
        ]
    )

    mismatches = manifest.validate_checksums()
    if mismatches:
        print(f"INTEGRITY CHECK FAILED: {len(mismatches)} issues")
        for m in mismatches:
            print(f"  {m}")
    else:
        print("All checksums valid")


if __name__ == "__main__":
    generate_sbom()
```

---

## Config Debugging

Debug configuration resolution from multiple sources.

```python
"""config_debug.py -- Trace configuration value origins."""
from pathlib import Path
from sniff.config import ConfigReconciler, ConfigSource


def debug_config():
    """Demonstrate config reconciliation."""
    reconciler = ConfigReconciler()

    # Simulate config from multiple sources
    reconciler.add_source(ConfigSource(
        key="batch_size",
        value=32,
        source="default",
        file_path=None,
        line_number=None,
        precedence=0,
    ))
    reconciler.add_source(ConfigSource(
        key="batch_size",
        value=64,
        source="file",
        file_path=Path("config.yaml"),
        line_number=12,
        precedence=1,
    ))
    reconciler.add_source(ConfigSource(
        key="batch_size",
        value=128,
        source="environment",
        file_path=None,
        line_number=None,
        precedence=2,
    ))
    reconciler.add_source(ConfigSource(
        key="batch_size",
        value=256,
        source="cli",
        file_path=None,
        line_number=None,
        precedence=3,
    ))

    # Explain resolution
    print(reconciler.explain("batch_size"))
    # Output:
    # Configuration for 'batch_size':
    #   default: 32
    #   file: 64 (from config.yaml:12)
    #   environment: 128
    #   cli: 256
    #   -> Final value: 256 (from cli)

    # Resolve programmatically
    final = reconciler.resolve("batch_size")
    print(f"\nFinal batch_size = {final.value} (from {final.source})")

    # List all tracked keys
    print(f"\nAll config keys: {reconciler.keys()}")

    # Show all sources for a key
    print(f"\nAll sources for batch_size:")
    for src in reconciler.all_sources("batch_size"):
        print(f"  [{src.precedence}] {src.source}: {src.value}")


if __name__ == "__main__":
    debug_config()
```

---

## CI/CD Environment Report

Generate a CI-friendly environment report.

```python
"""ci_report.py -- Generate environment report for CI logs."""
import json
from sniff.context import ExecutionContext


def ci_environment_report():
    """Print environment report suitable for CI logs."""
    ctx = ExecutionContext.capture(
        include_env_vars=False,  # Don't leak secrets
        include_hardware=True,
        include_packages=True,
    )

    print("=" * 60)
    print("ENVIRONMENT REPORT")
    print("=" * 60)

    # Platform
    plat = ctx.platform
    if hasattr(plat, 'os'):
        print(f"OS:       {plat.os} {plat.arch}")
    print(f"Python:   {ctx.command_line}")

    # Git
    git = ctx.workspace.git_info
    if git:
        print(f"Commit:   {git.commit_sha[:12]}")
        print(f"Branch:   {git.branch}")
        print(f"Dirty:    {git.is_dirty}")

    # CI
    ci = ctx.ci_info
    if hasattr(ci, 'is_ci') and ci.is_ci:
        print(f"CI:       {ci.provider}")

    # Hardware
    print(f"CPU:      {ctx.cpu_info.model}")
    print(f"Cores:    {ctx.cpu_info.cores}")
    print(f"Memory:   {ctx.memory_info.total_mb} MB")
    for gpu in ctx.gpu_info:
        print(f"GPU:      {gpu.vendor} {gpu.model}")

    # Fingerprint
    print(f"Fingerprint: {ctx.fingerprint()}")
    print("=" * 60)

    # Save full report as JSON artifact
    with open("environment-report.json", "w") as f:
        json.dump(ctx.to_dict(), f, indent=2)
    print("Full report saved to environment-report.json")


if __name__ == "__main__":
    ci_environment_report()
```

---

## Reproducibility Guard

Guard script execution against environment changes.

```python
"""repro_guard.py -- Verify environment before running experiments."""
import json
import sys
from pathlib import Path
from sniff.context import ExecutionContext


def check_reproducibility(baseline_path: str) -> bool:
    """Check current environment against a baseline.

    Returns True if compatible, False otherwise.
    """
    baseline_file = Path(baseline_path)
    if not baseline_file.exists():
        print(f"No baseline found at {baseline_path}")
        print("Run with --save-baseline to create one")
        return True

    with open(baseline_file) as f:
        baseline = ExecutionContext.from_dict(json.load(f))

    current = ExecutionContext.capture()
    diff = current.diff(baseline)

    if diff.is_compatible():
        print("Environment matches baseline")
        return True

    print("ENVIRONMENT MISMATCH DETECTED")
    print(diff.summary())
    return False


def save_baseline(path: str = "baseline_env.json"):
    """Save current environment as baseline."""
    ctx = ExecutionContext.capture()
    with open(path, "w") as f:
        json.dump(ctx.to_dict(), f, indent=2)
    print(f"Baseline saved: {path}")
    print(f"Fingerprint: {ctx.fingerprint()}")


if __name__ == "__main__":
    if "--save-baseline" in sys.argv:
        save_baseline()
    elif not check_reproducibility("baseline_env.json"):
        sys.exit(1)
```
