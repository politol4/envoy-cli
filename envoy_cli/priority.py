"""Priority management for secrets — assign, retrieve, and list priorities."""

from __future__ import annotations

from typing import Dict, List, Tuple

PRIORITY_LEVELS = ("low", "normal", "high", "critical")


class PriorityError(Exception):
    """Raised when a priority operation fails."""


def _meta_key(key: str) -> str:
    return f"__priority__{key}"


def set_priority(secrets: Dict[str, str], key: str, level: str) -> Dict[str, str]:
    """Assign a priority level to *key*. Returns updated secrets copy."""
    if key not in secrets:
        raise PriorityError(f"Key not found: {key!r}")
    level = level.lower()
    if level not in PRIORITY_LEVELS:
        raise PriorityError(
            f"Invalid priority {level!r}. Choose from: {', '.join(PRIORITY_LEVELS)}"
        )
    updated = dict(secrets)
    updated[_meta_key(key)] = level
    return updated


def remove_priority(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the priority metadata for *key*. Returns updated secrets copy."""
    if key not in secrets:
        raise PriorityError(f"Key not found: {key!r}")
    updated = dict(secrets)
    updated.pop(_meta_key(key), None)
    return updated


def get_priority(secrets: Dict[str, str], key: str) -> str | None:
    """Return the priority level for *key*, or None if not set."""
    if key not in secrets:
        raise PriorityError(f"Key not found: {key!r}")
    return secrets.get(_meta_key(key))


def list_by_priority(
    secrets: Dict[str, str],
) -> List[Tuple[str, str]]:
    """Return real keys sorted by priority (critical first, unset last).

    Returns a list of (key, level) tuples where level may be 'unset'.
    """
    order = {level: i for i, level in enumerate(reversed(PRIORITY_LEVELS))}
    real_keys = [
        k for k in secrets if not k.startswith("__priority__")
    ]
    result: List[Tuple[str, str]] = []
    for k in real_keys:
        level = secrets.get(_meta_key(k), "unset")
        result.append((k, level))

    result.sort(key=lambda t: order.get(t[1], len(PRIORITY_LEVELS)))
    return result
