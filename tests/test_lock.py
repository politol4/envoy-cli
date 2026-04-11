"""Tests for envoy_cli.lock (VaultLock)."""

from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from envoy_cli.lock import LockError, VaultLock


class TestVaultLock(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.vault_path = Path(self._tmp.name) / "test.vault"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_lock(self, stale_seconds: int = 30) -> VaultLock:
        return VaultLock(self.vault_path, stale_seconds=stale_seconds)

    # ------------------------------------------------------------------
    # Basic acquire / release
    # ------------------------------------------------------------------

    def test_not_locked_initially(self) -> None:
        self.assertFalse(self._make_lock().is_locked())

    def test_acquire_creates_lock_file(self) -> None:
        lock = self._make_lock()
        lock.acquire(owner="ci")
        self.assertTrue(lock.lock_path.exists())
        lock.release()

    def test_is_locked_after_acquire(self) -> None:
        lock = self._make_lock()
        lock.acquire()
        self.assertTrue(lock.is_locked())
        lock.release()

    def test_not_locked_after_release(self) -> None:
        lock = self._make_lock()
        lock.acquire()
        lock.release()
        self.assertFalse(lock.is_locked())

    def test_release_noop_when_not_locked(self) -> None:
        lock = self._make_lock()
        lock.release()  # should not raise

    # ------------------------------------------------------------------
    # Double-acquire raises
    # ------------------------------------------------------------------

    def test_second_acquire_raises_lock_error(self) -> None:
        lock = self._make_lock()
        lock.acquire(owner="alice")
        with self.assertRaises(LockError):
            lock.acquire(owner="bob")
        lock.release()

    def test_lock_error_message_contains_owner(self) -> None:
        lock = self._make_lock()
        lock.acquire(owner="alice")
        try:
            lock.acquire(owner="bob")
            self.fail("Expected LockError")
        except LockError as exc:
            self.assertIn("alice", str(exc))
        finally:
            lock.release()

    # ------------------------------------------------------------------
    # Stale lock handling
    # ------------------------------------------------------------------

    def test_stale_lock_auto_cleared(self) -> None:
        lock = self._make_lock(stale_seconds=0)
        lock.acquire(owner="old-process")
        time.sleep(0.05)
        # With stale_seconds=0 the lock should be treated as stale
        self.assertFalse(lock.is_locked())

    def test_stale_lock_allows_new_acquire(self) -> None:
        lock = self._make_lock(stale_seconds=0)
        lock.acquire(owner="old")
        time.sleep(0.05)
        lock.acquire(owner="new")  # should not raise
        lock.release()

    # ------------------------------------------------------------------
    # info() and lock file content
    # ------------------------------------------------------------------

    def test_info_returns_none_when_not_locked(self) -> None:
        self.assertIsNone(self._make_lock().info())

    def test_info_contains_owner(self) -> None:
        lock = self._make_lock()
        lock.acquire(owner="ci-bot")
        info = lock.info()
        self.assertIsNotNone(info)
        self.assertEqual(info["owner"], "ci-bot")
        lock.release()

    def test_info_contains_pid(self) -> None:
        import os
        lock = self._make_lock()
        lock.acquire()
        info = lock.info()
        self.assertEqual(info["pid"], os.getpid())
        lock.release()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def test_context_manager_releases_on_exit(self) -> None:
        lock = self._make_lock()
        with lock:
            self.assertTrue(lock.is_locked())
        self.assertFalse(lock.is_locked())

    def test_context_manager_releases_on_exception(self) -> None:
        lock = self._make_lock()
        try:
            with lock:
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        self.assertFalse(lock.is_locked())
