"""Archive old or unused secrets into a separate vault namespace."""

from __future__ import annotations

import time
from typing import Dict, List

ARCHIVE_PREFIX = "__archive__"


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


def _archive_key(key: str) -> str:
    return f"{ARCHIVE_PREFIX}{key}"


def _is_archived(key: str) -> bool:
    return key.startswith(ARCHIVE_PREFIX)


def archive_key(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Move *key* into the archive namespace and return updated secrets."""
    if not key:
        raise ArchiveError("Key must not be empty.")
    if _is_archived(key):
        raise ArchiveError(f"Key '{key}' is already archived.")
    if key not in secrets:
        raise ArchiveError(f"Key '{key}' not found in secrets.")

    updated = dict(secrets)
    updated[_archive_key(key)] = updated.pop(key)
    return updated


def unarchive_key(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Restore an archived key back to the live namespace."""
    if not key:
        raise ArchiveError("Key must not be empty.")
    archived = _archive_key(key)
    if archived not in secrets:
        raise ArchiveError(f"Key '{key}' is not archived.")
    live_key = key if not _is_archived(key) else key[len(ARCHIVE_PREFIX):]
    if live_key in secrets:
        raise ArchiveError(f"Key '{live_key}' already exists in live secrets.")

    updated = dict(secrets)
    updated[live_key] = updated.pop(archived)
    return updated


def list_archived(secrets: Dict[str, str]) -> List[str]:
    """Return the original (un-prefixed) names of all archived keys."""
    return sorted(
        key[len(ARCHIVE_PREFIX):]
        for key in secrets
        if _is_archived(key)
    )


def purge_archived(secrets: Dict[str, str]) -> Dict[str, str]:
    """Permanently delete all archived keys and return updated secrets."""
    return {k: v for k, v in secrets.items() if not _is_archived(k)}
