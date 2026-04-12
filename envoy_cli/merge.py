"""Merge secrets from one environment vault into another."""

from __future__ import annotations

from typing import Dict, List, Optional

from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


class MergeResult:
    """Summary of a completed merge operation."""

    def __init__(
        self,
        added: List[str],
        overwritten: List[str],
        skipped: List[str],
    ) -> None:
        self.added = added
        self.overwritten = overwritten
        self.skipped = skipped

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.overwritten)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "no changes"


def merge_vaults(
    src: Vault,
    dst: Vault,
    *,
    overwrite: bool = False,
    prefix: Optional[str] = None,
) -> MergeResult:
    """Merge secrets from *src* into *dst*.

    Args:
        src: Source vault to read secrets from.
        dst: Destination vault to write secrets into.
        overwrite: When *True*, existing keys in *dst* are overwritten.
        prefix: If given, only keys starting with this prefix are merged.

    Returns:
        A :class:`MergeResult` describing what changed.
    """
    src_secrets: Dict[str, str] = src.all()
    dst_secrets: Dict[str, str] = dst.all()

    added: List[str] = []
    overwritten: List[str] = []
    skipped: List[str] = []

    for key, value in src_secrets.items():
        if prefix and not key.startswith(prefix):
            continue
        if key in dst_secrets:
            if overwrite:
                dst.set(key, value)
                overwritten.append(key)
            else:
                skipped.append(key)
        else:
            dst.set(key, value)
            added.append(key)

    return MergeResult(added=added, overwritten=overwritten, skipped=skipped)
