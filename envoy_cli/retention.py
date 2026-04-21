"""Retention policy management for secrets.

Allows setting a maximum age (in days) for secrets. Secrets older than
the retention period are considered expired and can be purged.
"""
from __future__ import annotations

import time
from typing import Dict, List

RETENTION_META_PREFIX = "__retention__"


class RetentionError(Exception):
    """Raised when a retention operation fails."""


def _meta_key(key: str) -> str:
    return f"{RETENTION_META_PREFIX}{key}"


def set_retention(secrets: Dict[str, str], key: str, days: int) -> Dict[str, str]:
    """Attach a retention policy (in days) to *key*.

    Stores the policy as a meta-key alongside the creation timestamp so
    that expiry can be computed later.

    Raises RetentionError if *key* is not present or *days* is not positive.
    """
    if key not in secrets:
        raise RetentionError(f"Key '{key}' does not exist.")
    if days <= 0:
        raise RetentionError("Retention period must be a positive number of days.")

    created_at = int(time.time())
    policy = f"{days}:{created_at}"
    return {**secrets, _meta_key(key): policy}


def remove_retention(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove the retention policy attached to *key*.

    Raises RetentionError if no policy exists for *key*.
    """
    mk = _meta_key(key)
    if mk not in secrets:
        raise RetentionError(f"No retention policy set for '{key}'.")
    return {k: v for k, v in secrets.items() if k != mk}


def get_retention(secrets: Dict[str, str], key: str):
    """Return (days, created_at) for *key*, or None if not set."""
    mk = _meta_key(key)
    if mk not in secrets:
        return None
    days_str, ts_str = secrets[mk].split(":", 1)
    return int(days_str), int(ts_str)


def find_expired(secrets: Dict[str, str], now: float | None = None) -> List[str]:
    """Return a list of keys whose retention period has elapsed."""
    if now is None:
        now = time.time()

    expired: List[str] = []
    for key in list(secrets):
        if key.startswith(RETENTION_META_PREFIX):
            continue
        info = get_retention(secrets, key)
        if info is None:
            continue
        days, created_at = info
        age_days = (now - created_at) / 86400
        if age_days >= days:
            expired.append(key)
    return sorted(expired)


def purge_expired(secrets: Dict[str, str], now: float | None = None) -> Dict[str, str]:
    """Remove all expired keys (and their retention meta-keys) from *secrets*."""
    expired = find_expired(secrets, now=now)
    result = dict(secrets)
    for key in expired:
        result.pop(key, None)
        result.pop(_meta_key(key), None)
    return result
