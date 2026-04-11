"""Compare two environments and produce a structured diff report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_cli.diff import DiffResult, compute_diff
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


class CompareError(Exception):
    """Raised when a comparison cannot be completed."""


@dataclass
class CompareReport:
    """Holds the result of comparing two named environments."""

    env_a: str
    env_b: str
    diff: DiffResult
    warnings: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return self.diff.has_changes

    def summary(self) -> str:
        lines = [f"Comparing '{self.env_a}' vs '{self.env_b}':"]
        lines.extend(self.diff.as_lines())
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  ! {w}" for w in self.warnings)
        if not self.has_changes:
            lines.append("  Environments are identical.")
        return "\n".join(lines)


def compare_vaults(
    vault_a: Vault,
    vault_b: Vault,
    env_a: str = "A",
    env_b: str = "B",
    prefix: Optional[str] = None,
) -> CompareReport:
    """Compare two Vault instances and return a CompareReport."""
    secrets_a: Dict[str, str] = dict(vault_a.list())
    secrets_b: Dict[str, str] = dict(vault_b.list())

    if prefix:
        secrets_a = {k: v for k, v in secrets_a.items() if k.startswith(prefix)}
        secrets_b = {k: v for k, v in secrets_b.items() if k.startswith(prefix)}

    warnings: List[str] = []
    if not secrets_a:
        warnings.append(f"Environment '{env_a}' has no secrets (or none match prefix).")
    if not secrets_b:
        warnings.append(f"Environment '{env_b}' has no secrets (or none match prefix).")

    diff = compute_diff(secrets_a, secrets_b)
    return CompareReport(env_a=env_a, env_b=env_b, diff=diff, warnings=warnings)
