"""Snapshot: capture and restore vault state at a point in time."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .vault import Vault


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    created_at: float
    environment: str
    secrets: Dict[str, str]
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "environment": self.environment,
            "secrets": self.secrets,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            created_at=float(data["created_at"]),
            environment=str(data["environment"]),
            secrets=dict(data["secrets"]),
            note=str(data.get("note", "")),
        )


def take_snapshot(
    vault: Vault,
    passphrase: str,
    environment: str,
    note: str = "",
) -> Snapshot:
    """Decrypt *vault* and capture its current secrets as a Snapshot."""
    secrets = {k: vault.get(k, passphrase) for k in vault.list()}
    return Snapshot(
        created_at=time.time(),
        environment=environment,
        secrets=secrets,
        note=note,
    )


def restore_snapshot(
    snapshot: Snapshot,
    vault: Vault,
    passphrase: str,
) -> int:
    """Overwrite *vault* with the secrets stored in *snapshot*.

    Returns the number of secrets written.
    """
    for key, value in snapshot.secrets.items():
        vault.set(key, value, passphrase)
    return len(snapshot.secrets)


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Persist a snapshot to *path* as JSON."""
    path.write_text(json.dumps(snapshot.to_dict(), indent=2), encoding="utf-8")


def load_snapshot(path: Path) -> Snapshot:
    """Load a snapshot from a JSON file at *path*."""
    if not path.exists():
        raise SnapshotError(f"Snapshot file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Snapshot.from_dict(data)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Invalid snapshot file: {exc}") from exc
