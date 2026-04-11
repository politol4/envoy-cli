"""Vault locking: prevent concurrent writes by managing a lock file."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

LOCK_SUFFIX = ".lock"
STALE_SECONDS = 30


class LockError(Exception):
    """Raised when a vault lock cannot be acquired or released."""


class VaultLock:
    """Manages a simple file-based lock for a vault path."""

    def __init__(self, vault_path: str | Path, stale_seconds: int = STALE_SECONDS) -> None:
        self._lock_path = Path(str(vault_path) + LOCK_SUFFIX)
        self._stale_seconds = stale_seconds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    def acquire(self, owner: str = "") -> None:
        """Create the lock file.  Raises LockError if already locked."""
        if self._is_locked():
            info = self._read_info()
            raise LockError(
                f"Vault is locked by '{info.get('owner', 'unknown')}' "
                f"(PID {info.get('pid', '?')}).  "
                "Remove the lock file manually if the process has exited."
            )
        payload = {
            "owner": owner or os.environ.get("USER", "unknown"),
            "pid": os.getpid(),
            "acquired_at": time.time(),
        }
        self._lock_path.write_text(json.dumps(payload))

    def release(self) -> None:
        """Remove the lock file if it exists."""
        try:
            self._lock_path.unlink()
        except FileNotFoundError:
            pass

    def is_locked(self) -> bool:
        """Return True when a non-stale lock file exists."""
        return self._is_locked()

    def info(self) -> Optional[dict]:
        """Return the lock metadata dict, or None if no lock exists."""
        if not self._lock_path.exists():
            return None
        return self._read_info()

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "VaultLock":
        self.acquire()
        return self

    def __exit__(self, *_) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_locked(self) -> bool:
        if not self._lock_path.exists():
            return False
        info = self._read_info()
        age = time.time() - info.get("acquired_at", 0)
        if age > self._stale_seconds:
            # Stale lock — remove it automatically
            self.release()
            return False
        return True

    def _read_info(self) -> dict:
        try:
            return json.loads(self._lock_path.read_text())
        except Exception:
            return {}
