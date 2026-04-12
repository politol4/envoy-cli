"""Cascade: apply a set of secrets from a base environment into a target environment,
only filling in keys that are missing in the target (non-destructive merge)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .vault import Vault


class CascadeError(Exception):
    """Raised when a cascade operation cannot be completed."""


@dataclass
class CascadeResult:
    added: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} key(s) added")
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) skipped (already present)")
        return ", ".join(parts) if parts else "no changes"

    def as_lines(self) -> List[str]:
        lines: List[str] = []
        for k in sorted(self.added):
            lines.append(f"  + {k}")
        for k in sorted(self.skipped):
            lines.append(f"  ~ {k} (skipped)")
        return lines


def cascade(
    source_secrets: Dict[str, str],
    target_vault: Vault,
    passphrase: str,
    prefix: str = "",
) -> CascadeResult:
    """Copy keys from *source_secrets* into *target_vault* for any key not
    already present in the target.  Optionally restrict to keys that start
    with *prefix*.

    The target vault is mutated in-place (caller must save it).
    """
    if not source_secrets:
        raise CascadeError("source secrets must not be empty")

    result = CascadeResult()
    target_secrets = target_vault.all()

    for key, value in source_secrets.items():
        if prefix and not key.startswith(prefix):
            continue
        if key in target_secrets:
            result.skipped.append(key)
        else:
            target_vault.set(key, value, passphrase)
            result.added.append(key)

    return result
