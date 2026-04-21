"""Bookmark frequently-used secret keys for quick access."""
from __future__ import annotations

from typing import Dict, List

BOOKMARK_META_PREFIX = "__bookmark__"


class BookmarkError(Exception):
    """Raised when a bookmark operation fails."""


def _meta_key(key: str) -> str:
    return f"{BOOKMARK_META_PREFIX}{key}"


def add_bookmark(secrets: Dict[str, str], key: str, note: str = "") -> Dict[str, str]:
    """Bookmark *key*, optionally storing a human-readable *note*."""
    if key not in secrets:
        raise BookmarkError(f"Key '{key}' does not exist in secrets.")
    updated = dict(secrets)
    updated[_meta_key(key)] = note
    return updated


def remove_bookmark(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the bookmark for *key*."""
    meta = _meta_key(key)
    if meta not in secrets:
        raise BookmarkError(f"Key '{key}' is not bookmarked.")
    updated = dict(secrets)
    del updated[meta]
    return updated


def is_bookmarked(secrets: Dict[str, str], key: str) -> bool:
    """Return True if *key* is currently bookmarked."""
    return _meta_key(key) in secrets


def list_bookmarks(secrets: Dict[str, str]) -> List[Dict[str, str]]:
    """Return a list of dicts with 'key' and 'note' for every bookmarked key."""
    results = []
    for raw_key, note in secrets.items():
        if raw_key.startswith(BOOKMARK_META_PREFIX):
            original = raw_key[len(BOOKMARK_META_PREFIX):]
            results.append({"key": original, "note": note})
    return sorted(results, key=lambda d: d["key"])
