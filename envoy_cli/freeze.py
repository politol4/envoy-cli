"""Freeze/unfreeze secrets to prevent accidental modification."""

from __future__ import annotations

FREEZE_META_PREFIX = "__freeze__."


class FreezeError(Exception):
    pass


def _meta_key(key: str) -> str:
    return f"{FREEZE_META_PREFIX}{key}"


def freeze_key(secrets: dict, key: str) -> dict:
    """Mark a key as frozen. Raises FreezeError if key does not exist."""
    if key not in secrets:
        raise FreezeError(f"Key '{key}' not found.")
    updated = dict(secrets)
    updated[_meta_key(key)] = "frozen"
    return updated


def unfreeze_key(secrets: dict, key: str) -> dict:
    """Remove freeze marker from a key."""
    meta = _meta_key(key)
    if meta not in secrets:
        raise FreezeError(f"Key '{key}' is not frozen.")
    updated = dict(secrets)
    del updated[meta]
    return updated


def is_frozen(secrets: dict, key: str) -> bool:
    return _meta_key(key) in secrets


def list_frozen(secrets: dict) -> list[str]:
    """Return sorted list of frozen keys."""
    result = []
    for k in secrets:
        if k.startswith(FREEZE_META_PREFIX):
            original = k[len(FREEZE_META_PREFIX):]
            result.append(original)
    return sorted(result)


def guard_frozen(secrets: dict, key: str) -> None:
    """Raise FreezeError if the key is frozen."""
    if is_frozen(secrets, key):
        raise FreezeError(f"Key '{key}' is frozen and cannot be modified. Unfreeze it first.")
