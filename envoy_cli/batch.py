"""Batch operations: set or delete multiple secrets at once."""

from __future__ import annotations

from typing import Dict, List, Tuple

from envoy_cli.sync import SyncManager


class BatchError(Exception):
    """Raised when a batch operation fails."""


BatchResult = Tuple[List[str], List[str]]  # (applied_keys, skipped_keys)


def batch_set(
    manager: SyncManager,
    env: str,
    passphrase: str,
    pairs: Dict[str, str],
    *,
    overwrite: bool = True,
) -> BatchResult:
    """Set multiple key/value pairs in one operation.

    Args:
        manager: SyncManager instance.
        env: Environment name (e.g. 'staging').
        passphrase: Vault passphrase.
        pairs: Mapping of key -> value to store.
        overwrite: If False, existing keys are skipped.

    Returns:
        Tuple of (applied_keys, skipped_keys).
    """
    if not pairs:
        raise BatchError("pairs must not be empty")

    vault = manager._load_vault(env, passphrase)
    applied: List[str] = []
    skipped: List[str] = []

    for key, value in pairs.items():
        if not key:
            raise BatchError("key must not be empty")
        if not overwrite and vault.get(key) is not None:
            skipped.append(key)
            continue
        vault.set(key, value)
        applied.append(key)

    vault.save()
    return applied, skipped


def batch_delete(
    manager: SyncManager,
    env: str,
    passphrase: str,
    keys: List[str],
    *,
    ignore_missing: bool = False,
) -> BatchResult:
    """Delete multiple keys in one operation.

    Args:
        manager: SyncManager instance.
        env: Environment name.
        passphrase: Vault passphrase.
        keys: List of keys to delete.
        ignore_missing: If True, missing keys are skipped instead of raising.

    Returns:
        Tuple of (deleted_keys, missing_keys).
    """
    if not keys:
        raise BatchError("keys must not be empty")

    vault = manager._load_vault(env, passphrase)
    deleted: List[str] = []
    missing: List[str] = []

    for key in keys:
        if vault.get(key) is None:
            if ignore_missing:
                missing.append(key)
                continue
            raise BatchError(f"key not found: {key}")
        vault.delete(key)
        deleted.append(key)

    vault.save()
    return deleted, missing
