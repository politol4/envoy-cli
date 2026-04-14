"""Dependency tracking between secrets.

Allows marking that one secret key depends on another, so that
changes to a depended-upon key can surface warnings.
"""
from __future__ import annotations

from typing import Dict, List

DEPENDS_PREFIX = "__dep__."


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


def _meta_key(key: str) -> str:
    return f"{DEPENDS_PREFIX}{key}"


def add_dependency(secrets: Dict[str, str], key: str, depends_on: str) -> Dict[str, str]:
    """Record that *key* depends on *depends_on*.

    Both keys must already exist in *secrets*.
    A key may not depend on itself.
    Returns an updated copy of *secrets*.
    """
    if key not in secrets:
        raise DependencyError(f"Key not found: {key!r}")
    if depends_on not in secrets:
        raise DependencyError(f"Dependency key not found: {depends_on!r}")
    if key == depends_on:
        raise DependencyError("A key cannot depend on itself.")

    updated = dict(secrets)
    meta = _meta_key(key)
    existing = [d for d in updated.get(meta, "").split(",") if d]
    if depends_on not in existing:
        existing.append(depends_on)
    updated[meta] = ",".join(sorted(existing))
    return updated


def remove_dependency(secrets: Dict[str, str], key: str, depends_on: str) -> Dict[str, str]:
    """Remove the dependency of *key* on *depends_on*."""
    updated = dict(secrets)
    meta = _meta_key(key)
    existing = [d for d in updated.get(meta, "").split(",") if d]
    if depends_on not in existing:
        raise DependencyError(
            f"{key!r} does not depend on {depends_on!r}."
        )
    existing.remove(depends_on)
    if existing:
        updated[meta] = ",".join(sorted(existing))
    else:
        updated.pop(meta, None)
    return updated


def get_dependencies(secrets: Dict[str, str], key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    meta = _meta_key(key)
    raw = secrets.get(meta, "")
    return [d for d in raw.split(",") if d]


def find_dependents(secrets: Dict[str, str], key: str) -> List[str]:
    """Return all keys that declare a dependency on *key*."""
    result = []
    for k, v in secrets.items():
        if not k.startswith(DEPENDS_PREFIX):
            continue
        deps = [d for d in v.split(",") if d]
        if key in deps:
            owner = k[len(DEPENDS_PREFIX):]
            result.append(owner)
    return sorted(result)
