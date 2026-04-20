"""Scope support: restrict secret visibility to a named scope (e.g. 'backend', 'frontend')."""
from __future__ import annotations

from typing import Dict, List

SCOPE_META_PREFIX = "__scope__"


class ScopeError(Exception):
    """Raised when a scope operation fails."""


def _meta_key(key: str) -> str:
    return f"{SCOPE_META_PREFIX}{key}"


def set_scope(secrets: Dict[str, str], key: str, scope: str) -> Dict[str, str]:
    """Assign *scope* to *key*.  Returns an updated copy of *secrets*."""
    if not key:
        raise ScopeError("key must not be empty")
    if not scope:
        raise ScopeError("scope must not be empty")
    if key not in secrets:
        raise ScopeError(f"key '{key}' not found in secrets")
    updated = dict(secrets)
    updated[_meta_key(key)] = scope
    return updated


def remove_scope(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove scope metadata for *key*.  Returns an updated copy of *secrets*."""
    updated = dict(secrets)
    meta = _meta_key(key)
    if meta not in updated:
        raise ScopeError(f"key '{key}' has no scope assigned")
    del updated[meta]
    return updated


def get_scope(secrets: Dict[str, str], key: str) -> str | None:
    """Return the scope for *key*, or ``None`` if not set."""
    return secrets.get(_meta_key(key))


def keys_in_scope(secrets: Dict[str, str], scope: str) -> List[str]:
    """Return all *non-meta* keys whose scope matches *scope*."""
    if not scope:
        raise ScopeError("scope must not be empty")
    result = []
    for k, v in secrets.items():
        if k.startswith(SCOPE_META_PREFIX):
            continue
        if secrets.get(_meta_key(k)) == scope:
            result.append(k)
    return sorted(result)


def list_scopes(secrets: Dict[str, str]) -> List[str]:
    """Return a sorted, deduplicated list of all scopes currently in use."""
    seen = set()
    for k, v in secrets.items():
        if k.startswith(SCOPE_META_PREFIX):
            seen.add(v)
    return sorted(seen)
