"""TTL (time-to-live) support for secrets in the vault."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

TTL_META_PREFIX = "__ttl__"


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _meta_key(secret_key: str) -> str:
    return f"{TTL_META_PREFIX}{secret_key}"


def set_ttl(secrets: Dict[str, str], key: str, seconds: int) -> Dict[str, str]:
    """Attach a TTL (Unix expiry timestamp) to *key*.

    Raises TTLError if *key* is not present or *seconds* is not positive.
    """
    if key not in secrets:
        raise TTLError(f"Key '{key}' not found in secrets.")
    if seconds <= 0:
        raise TTLError("TTL must be a positive integer number of seconds.")
    expiry = int(time.time()) + seconds
    updated = dict(secrets)
    updated[_meta_key(key)] = str(expiry)
    return updated


def get_ttl(secrets: Dict[str, str], key: str) -> Optional[int]:
    """Return remaining seconds for *key*, or None if no TTL is set."""
    meta = secrets.get(_meta_key(key))
    if meta is None:
        return None
    remaining = int(meta) - int(time.time())
    return max(remaining, 0)


def remove_ttl(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the TTL entry for *key* (no-op if not set)."""
    updated = dict(secrets)
    updated.pop(_meta_key(key), None)
    return updated


def purge_expired(secrets: Dict[str, str]) -> Dict[str, str]:
    """Remove all secrets (and their TTL metadata) that have expired."""
    now = int(time.time())
    expired_keys: List[str] = []
    for key, value in secrets.items():
        if key.startswith(TTL_META_PREFIX):
            continue
        meta = secrets.get(_meta_key(key))
        if meta is not None and int(meta) <= now:
            expired_keys.append(key)

    updated = dict(secrets)
    for key in expired_keys:
        updated.pop(key, None)
        updated.pop(_meta_key(key), None)
    return updated


def list_expiring(secrets: Dict[str, str], within_seconds: int = 3600) -> List[str]:
    """Return keys whose TTL will expire within *within_seconds*."""
    now = int(time.time())
    result: List[str] = []
    for key in secrets:
        if key.startswith(TTL_META_PREFIX):
            continue
        meta = secrets.get(_meta_key(key))
        if meta is not None:
            expiry = int(meta)
            if expiry - now <= within_seconds:
                result.append(key)
    return sorted(result)
