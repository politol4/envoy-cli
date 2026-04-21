"""Category management for grouping secrets by logical domain."""

from __future__ import annotations

from typing import Dict, List

CATEGORY_META_PREFIX = "__category__"


class CategoryError(Exception):
    """Raised when a category operation fails."""


def _meta_key(key: str) -> str:
    return f"{CATEGORY_META_PREFIX}{key}"


def set_category(secrets: Dict[str, str], key: str, category: str) -> Dict[str, str]:
    """Assign *key* to *category*. Raises CategoryError if key is missing."""
    if not category or not category.strip():
        raise CategoryError("category name must not be empty")
    if key not in secrets:
        raise CategoryError(f"key not found: {key!r}")
    updated = dict(secrets)
    updated[_meta_key(key)] = category.strip()
    return updated


def remove_category(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the category assignment for *key*."""
    meta = _meta_key(key)
    if meta not in secrets:
        raise CategoryError(f"no category set for key: {key!r}")
    updated = dict(secrets)
    del updated[meta]
    return updated


def get_category(secrets: Dict[str, str], key: str) -> str | None:
    """Return the category for *key*, or None if unset."""
    return secrets.get(_meta_key(key))


def list_by_category(secrets: Dict[str, str]) -> Dict[str, List[str]]:
    """Return a mapping of category -> sorted list of keys that belong to it."""
    result: Dict[str, List[str]] = {}
    for k, v in secrets.items():
        if k.startswith(CATEGORY_META_PREFIX):
            original_key = k[len(CATEGORY_META_PREFIX):]
            result.setdefault(v, []).append(original_key)
    for keys in result.values():
        keys.sort()
    return result
