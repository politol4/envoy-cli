"""Tests for envoy_cli.lock_commands."""

from __future__ import annotations

import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from envoy_cli.lock import LockError, VaultLock
from envoy_cli.lock_commands import cmd_lock_acquire, cmd_lock_release, cmd_lock_status


def _make_args(tmp_dir: str, env: str = "default", owner: str = "") -> types.SimpleNamespace:
    return types.SimpleNamespace(
        env=env,
        vault_dir=Path(tmp_dir),
        owner=owner,
    )


class TestCmdLockStatus(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_not_locked_message(self) -> None:
        args = _make_args(self._tmp.name)
        result = cmd_lock_status(args)
        self.assertIn("not locked", result.lower())

    def test_locked_message_contains_owner(self) -> None:
        args = _make_args(self._tmp.name, owner="ci")
        cmd_lock_acquire(args)
        result = cmd_lock_status(args)
        self.assertIn("LOCKED", result)
        cmd_lock_release(args)

    def test_locked_message_contains_vault_name(self) -> None:
        args = _make_args(self._tmp.name, env="staging")
        cmd_lock_acquire(args)
        result = cmd_lock_status(args)
        self.assertIn("staging.vault", result)
        cmd_lock_release(args)


class TestCmdLockAcquire(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_acquire_returns_success_message(self) -> None:
        args = _make_args(self._tmp.name)
        result = cmd_lock_acquire(args)
        self.assertIn("acquired", result.lower())
        cmd_lock_release(args)

    def test_double_acquire_raises_lock_error(self) -> None:
        args = _make_args(self._tmp.name, owner="first")
        cmd_lock_acquire(args)
        with self.assertRaises(LockError):
            cmd_lock_acquire(args)
        cmd_lock_release(args)

    def test_lock_file_created_on_disk(self) -> None:
        args = _make_args(self._tmp.name, env="prod")
        cmd_lock_acquire(args)
        lock_path = Path(self._tmp.name) / "prod.vault.lock"
        self.assertTrue(lock_path.exists())
        cmd_lock_release(args)


class TestCmdLockRelease(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_release_not_locked_returns_noop_message(self) -> None:
        args = _make_args(self._tmp.name)
        result = cmd_lock_release(args)
        self.assertIn("not locked", result.lower())

    def test_release_after_acquire_succeeds(self) -> None:
        args = _make_args(self._tmp.name)
        cmd_lock_acquire(args)
        result = cmd_lock_release(args)
        self.assertIn("released", result.lower())

    def test_vault_unlocked_after_release(self) -> None:
        args = _make_args(self._tmp.name, env="dev")
        cmd_lock_acquire(args)
        cmd_lock_release(args)
        vault_path = Path(self._tmp.name) / "dev.vault"
        lock = VaultLock(vault_path)
        self.assertFalse(lock.is_locked())
