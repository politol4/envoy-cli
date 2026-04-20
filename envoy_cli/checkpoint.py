"""checkpoint.py — Named checkpoints for vault state.

A checkpoint is a lightweight, labelled marker that records the current
vault secret count and timestamp without storing the full encrypted payload
(unlike a snapshot).  Checkpoints are useful for quickly auditing *when*
a vault was last known to be in a particular state.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class CheckpointError(Exception):
    """Raised when a checkpoint operation fails."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Checkpoint:
    label: str
    env: str
    secret_count: int
    created_at: float = field(default_factory=time.time)
    notes: str = ""

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "env": self.env,
            "secret_count": self.secret_count,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Checkpoint":
        for required in ("label", "env", "secret_count", "created_at"):
            if required not in data:
                raise CheckpointError(f"Checkpoint data missing field: {required!r}")
        return cls(
            label=data["label"],
            env=data["env"],
            secret_count=int(data["secret_count"]),
            created_at=float(data["created_at"]),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _checkpoints_path(directory: str) -> str:
    return os.path.join(directory, "checkpoints.json")


def _load_all(directory: str) -> List[Checkpoint]:
    """Load all checkpoints from *directory*.  Returns [] if none exist."""
    path = _checkpoints_path(directory)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [Checkpoint.from_dict(item) for item in raw]


def _save_all(directory: str, checkpoints: List[Checkpoint]) -> None:
    os.makedirs(directory, exist_ok=True)
    path = _checkpoints_path(directory)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([c.to_dict() for c in checkpoints], fh, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_checkpoint(
    directory: str,
    label: str,
    env: str,
    secret_count: int,
    notes: str = "",
) -> Checkpoint:
    """Create a new checkpoint, replacing any existing one with the same label."""
    if not label or not label.strip():
        raise CheckpointError("Checkpoint label must not be empty.")
    if not env or not env.strip():
        raise CheckpointError("Checkpoint env must not be empty.")

    checkpoints = [c for c in _load_all(directory) if c.label != label]
    cp = Checkpoint(label=label, env=env, secret_count=secret_count, notes=notes)
    checkpoints.append(cp)
    _save_all(directory, checkpoints)
    return cp


def get_checkpoint(directory: str, label: str) -> Optional[Checkpoint]:
    """Return the checkpoint with *label*, or None if it does not exist."""
    for cp in _load_all(directory):
        if cp.label == label:
            return cp
    return None


def list_checkpoints(directory: str) -> List[Checkpoint]:
    """Return all checkpoints sorted by creation time (oldest first)."""
    return sorted(_load_all(directory), key=lambda c: c.created_at)


def delete_checkpoint(directory: str, label: str) -> bool:
    """Delete the checkpoint with *label*.  Returns True if it existed."""
    before = _load_all(directory)
    after = [c for c in before if c.label != label]
    if len(after) == len(before):
        return False
    _save_all(directory, after)
    return True
