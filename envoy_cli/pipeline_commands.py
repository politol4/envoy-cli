"""CLI command handlers for the pipeline feature."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .pipeline import PipelineError, PipelineStep, run_pipeline
from .sync import SyncManager


def _make_manager(args: Any) -> SyncManager:
    return SyncManager(
        vault_dir=getattr(args, "vault_dir", "."),
        passphrase=args.passphrase,
    )


def _load_steps(path: str) -> list[PipelineStep]:
    """Read a JSON file that contains a list of step dicts."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise PipelineError("Pipeline file must contain a JSON array of steps")
    return [PipelineStep.from_dict(item) for item in data]


def cmd_pipeline_run(args: Any) -> str:
    """Execute a pipeline file against a local vault environment."""
    manager = _make_manager(args)
    steps = _load_steps(args.file)
    vault = manager._load_vault(args.env)
    secrets = vault.all()

    stop = getattr(args, "stop_on_error", False)
    result = run_pipeline(secrets, steps, stop_on_error=stop)

    for key, value in secrets.items():
        vault.set(key, value)

    manager._save_vault(args.env, vault)

    lines = [f"Pipeline complete: {result.summary()}"]
    if result.applied:
        lines.append("  Applied: " + ", ".join(result.applied))
    if result.skipped:
        lines.append("  Skipped: " + ", ".join(result.skipped))
    if result.errors:
        lines.append("  Errors:  " + "; ".join(result.errors))
    return "\n".join(lines)


def cmd_pipeline_validate(args: Any) -> str:
    """Validate a pipeline file without executing it."""
    try:
        steps = _load_steps(args.file)
    except (PipelineError, json.JSONDecodeError, OSError) as exc:
        return f"Invalid pipeline: {exc}"

    issues: list[str] = []
    for i, step in enumerate(steps):
        if not step.action:
            issues.append(f"Step {i}: empty action")
        if step.action not in {"set", "delete", "rename", "copy"}:
            issues.append(f"Step {i}: unknown action '{step.action}'")

    if issues:
        return "Validation failed:\n" + "\n".join(f"  - {m}" for m in issues)
    return f"Pipeline is valid ({len(steps)} step(s))"
