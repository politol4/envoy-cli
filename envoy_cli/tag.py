"""Tag management for vault secrets — attach, remove, and filter by tags."""

from __future__ import annotations

from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when a tagging operation fails."""


_TAG_META_PREFIX = "__tags__."


def _meta_key(secret_key: str) -> str:
    return f"{_TAG_META_PREFIX}{secret_key}"


def add_tag(secrets: Dict[str, str], key: str, tag: str) -> None:
    """Add *tag* to *key*.  Creates the tag list if it does not exist."""
    if key not in secrets:
        raise TagError(f"Secret '{key}' does not exist.")
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must not be empty.")
    meta_key = _meta_key(key)
    existing = _get_tags(secrets, key)
    if tag not in existing:
        existing.append(tag)
    secrets[meta_key] = ",".join(existing)


def remove_tag(secrets: Dict[str, str], key: str, tag: str) -> None:
    """Remove *tag* from *key*.  Silently succeeds if tag is absent."""
    if key not in secrets:
        raise TagError(f"Secret '{key}' does not exist.")
    meta_key = _meta_key(key)
    existing = _get_tags(secrets, key)
    updated = [t for t in existing if t != tag]
    if updated:
        secrets[meta_key] = ",".join(updated)
    else:
        secrets.pop(meta_key, None)


def _get_tags(secrets: Dict[str, str], key: str) -> List[str]:
    """Return the list of tags for *key* (may be empty)."""
    raw = secrets.get(_meta_key(key), "")
    return [t for t in raw.split(",") if t]


def get_tags(secrets: Dict[str, str], key: str) -> List[str]:
    """Public accessor — returns tags for *key* or raises TagError if missing."""
    if key not in secrets:
        raise TagError(f"Secret '{key}' does not exist.")
    return _get_tags(secrets, key)


def filter_by_tag(
    secrets: Dict[str, str], tag: str
) -> Dict[str, str]:
    """Return a dict of secrets (excluding meta-keys) whose tag list contains *tag*."""
    return {
        k: v
        for k, v in secrets.items()
        if not k.startswith(_TAG_META_PREFIX) and tag in _get_tags(secrets, k)
    }


def list_all_tags(secrets: Dict[str, str]) -> List[str]:
    """Return a sorted, deduplicated list of every tag used across all secrets."""
    seen: set = set()
    for k in secrets:
        if k.startswith(_TAG_META_PREFIX):
            for t in secrets[k].split(","):
                if t:
                    seen.add(t)
    return sorted(seen)
