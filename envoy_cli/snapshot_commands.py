"""CLI command handlers for snapshot operations."""
from __future__ import annotations

import time
from pathlib import Path

from .snapshot import (
    SnapshotError,
    load_snapshot,
    restore_snapshot,
    save_snapshot,
    take_snapshot,
)
from .sync import SyncManager


def cmd_snapshot_take(args, manager: SyncManager) -> str:
    """Take a snapshot of the current vault and write it to a file."""
    vault = manager._load_vault(args.env)
    passphrase = args.passphrase
    environment = args.env
    note = getattr(args, "note", "")

    snapshot = take_snapshot(vault, passphrase, environment, note=note)
    out_path = Path(args.output) if args.output else _default_path(environment)
    save_snapshot(snapshot, out_path)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(snapshot.created_at))
    return f"Snapshot taken at {ts} → {out_path} ({len(snapshot.secrets)} secrets)"


def cmd_snapshot_restore(args, manager: SyncManager) -> str:
    """Restore a vault from a snapshot file."""
    in_path = Path(args.input)
    try:
        snapshot = load_snapshot(in_path)
    except SnapshotError as exc:
        raise SystemExit(f"error: {exc}") from exc

    vault = manager._load_vault(args.env)
    count = restore_snapshot(snapshot, vault, args.passphrase)
    manager._save_vault(args.env, vault)
    return f"Restored {count} secrets from {in_path} into '{args.env}' environment"


def cmd_snapshot_inspect(args) -> str:
    """Print metadata and keys stored in a snapshot file."""
    in_path = Path(args.input)
    try:
        snapshot = load_snapshot(in_path)
    except SnapshotError as exc:
        raise SystemExit(f"error: {exc}") from exc

    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(snapshot.created_at))
    lines = [
        f"Environment : {snapshot.environment}",
        f"Created at  : {ts}",
        f"Note        : {snapshot.note or '(none)'}",
        f"Secrets     : {len(snapshot.secrets)}",
        "",
    ]
    for key in sorted(snapshot.secrets):
        lines.append(f"  {key}")
    return "\n".join(lines)


def _default_path(environment: str) -> Path:
    ts = time.strftime("%Y%m%dT%H%M%S")
    return Path(f"{environment}_{ts}.snapshot.json")
