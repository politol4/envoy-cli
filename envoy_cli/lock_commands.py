"""CLI command handlers for vault lock inspection and manual release."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from envoy_cli.lock import LockError, VaultLock


def _vault_path_from_args(args: Any) -> Path:
    """Resolve vault path from parsed CLI args (mirrors sync.py convention)."""
    env = getattr(args, "env", "default")
    base = Path(getattr(args, "vault_dir", Path.home() / ".envoy"))
    return base / f"{env}.vault"


def cmd_lock_status(args: Any) -> str:
    """Report whether the vault is currently locked."""
    vault_path = _vault_path_from_args(args)
    lock = VaultLock(vault_path)
    info = lock.info()
    if info is None:
        return f"Vault '{vault_path.name}' is not locked."
    age = int(time.time() - info.get("acquired_at", time.time()))
    return (
        f"Vault '{vault_path.name}' is LOCKED\n"
        f"  Owner : {info.get('owner', 'unknown')}\n"
        f"  PID   : {info.get('pid', '?')}\n"
        f"  Age   : {age}s"
    )


def cmd_lock_acquire(args: Any) -> str:
    """Manually acquire a lock on the vault (for scripting / CI use)."""
    vault_path = _vault_path_from_args(args)
    owner = getattr(args, "owner", "") or ""
    lock = VaultLock(vault_path)
    try:
        lock.acquire(owner=owner)
    except LockError as exc:
        raise LockError(str(exc)) from exc
    return f"Lock acquired on '{vault_path.name}'."


def cmd_lock_release(args: Any) -> str:
    """Manually release a lock on the vault."""
    vault_path = _vault_path_from_args(args)
    lock = VaultLock(vault_path)
    if not lock.is_locked():
        return f"Vault '{vault_path.name}' was not locked — nothing to do."
    lock.release()
    return f"Lock released on '{vault_path.name}'."
