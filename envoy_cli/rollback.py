"""rollback.py — Restore a vault to a previous snapshot by index or label."""

from __future__ import annotations

import os
from typing import List

from envoy_cli.snapshot import Snapshot, from_dict, SnapshotError
from envoy_cli.vault import Vault


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


def list_snapshots(snapshot_dir: str, env: str) -> List[Snapshot]:
    """Return all snapshots for *env* found in *snapshot_dir*, oldest first."""
    if not os.path.isdir(snapshot_dir):
        return []

    snapshots: List[Snapshot] = []
    for fname in sorted(os.listdir(snapshot_dir)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(snapshot_dir, fname)
        try:
            import json
            with open(fpath, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            snap = from_dict(data)
            if snap.env == env:
                snapshots.append(snap)
        except (SnapshotError, KeyError, ValueError):
            continue
    return snapshots


def rollback_to_index(vault: Vault, snapshots: List[Snapshot], index: int) -> int:
    """Overwrite *vault* secrets with those from *snapshots[index]*.

    Returns the number of keys restored.

    Raises:
        RollbackError: if *index* is out of range or snapshot list is empty.
    """
    if not snapshots:
        raise RollbackError("No snapshots available to roll back to.")
    if index < 0 or index >= len(snapshots):
        raise RollbackError(
            f"Index {index} is out of range (0–{len(snapshots) - 1})."
        )

    target = snapshots[index]
    # Clear existing secrets and replace with snapshot contents
    for key in list(vault.all().keys()):
        vault.delete(key)
    for key, value in target.secrets.items():
        vault.set(key, value)
    vault.save()
    return len(target.secrets)


def rollback_to_label(vault: Vault, snapshots: List[Snapshot], label: str) -> int:
    """Find the most-recent snapshot whose *label* matches and roll back to it.

    Raises:
        RollbackError: if no snapshot with the given label is found.
    """
    # Search newest-first
    for snap in reversed(snapshots):
        if snap.label == label:
            idx = snapshots.index(snap)
            return rollback_to_index(vault, snapshots, idx)
    raise RollbackError(f"No snapshot found with label '{label}'.")
