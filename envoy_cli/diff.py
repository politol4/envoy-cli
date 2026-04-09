"""Diff utilities for comparing .env variable sets."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DiffResult:
    """Represents the diff between two sets of environment variables."""

    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes."
        return ", ".join(parts)

    def as_lines(self, mask_values: bool = True) -> List[str]:
        """Return a human-readable list of diff lines."""
        lines = []
        for key, val in sorted(self.added.items()):
            display = "***" if mask_values else val
            lines.append(f"+ {key}={display}")
        for key, val in sorted(self.removed.items()):
            display = "***" if mask_values else val
            lines.append(f"- {key}={display}")
        for key, (old, new) in sorted(self.changed.items()):
            if mask_values:
                lines.append(f"~ {key}=*** -> ***")
            else:
                lines.append(f"~ {key}={old!r} -> {new!r}")
        return lines


def compute_diff(
    local: Dict[str, str],
    remote: Dict[str, str],
) -> DiffResult:
    """Compute the diff between local and remote env variable dicts."""
    result = DiffResult()
    all_keys = set(local) | set(remote)
    for key in all_keys:
        in_local = key in local
        in_remote = key in remote
        if in_local and not in_remote:
            result.added[key] = local[key]
        elif in_remote and not in_local:
            result.removed[key] = remote[key]
        elif local[key] != remote[key]:
            result.changed[key] = (local[key], remote[key])
        else:
            result.unchanged[key] = local[key]
    return result
