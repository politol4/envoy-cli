"""Pin secrets to a specific version/value, preventing accidental overwrites."""

from __future__ import annotations

from typing import Dict, List

PIN_META_PREFIX = "__pin__"


class PinError(Exception):
    """Raised when a pin operation fails."""


def _meta_key(key: str) -> str:
    return f"{PIN_META_PREFIX}{key}"


def pin_key(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Mark *key* as pinned so that sync/import will not overwrite it."""
    if key not in secrets:
        raise PinError(f"Key '{key}' does not exist in secrets.")
    meta = _meta_key(key)
    if secrets.get(meta) == "pinned":
        raise PinError(f"Key '{key}' is already pinned.")
    updated = dict(secrets)
    updated[meta] = "pinned"
    return updated


def unpin_key(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the pin from *key*."""
    meta = _meta_key(key)
    if meta not in secrets:
        raise PinError(f"Key '{key}' is not pinned.")
    updated = dict(secrets)
    del updated[meta]
    return updated


def is_pinned(secrets: Dict[str, str], key: str) -> bool:
    """Return True if *key* is currently pinned."""
    return secrets.get(_meta_key(key)) == "pinned"


def list_pinned(secrets: Dict[str, str]) -> List[str]:
    """Return a sorted list of all pinned keys (excluding meta entries)."""
    return sorted(
        key
        for key in secrets
        if not key.startswith(PIN_META_PREFIX)
        and is_pinned(secrets, key)
    )


def filter_unpinned(incoming: Dict[str, str], secrets: Dict[str, str]) -> Dict[str, str]:
    """Return *incoming* with pinned keys removed so they are not overwritten."""
    return {k: v for k, v in incoming.items() if not is_pinned(secrets, k)}
