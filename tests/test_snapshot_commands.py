"""Tests for envoy_cli.snapshot_commands."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from envoy_cli.snapshot import Snapshot, save_snapshot
from envoy_cli.snapshot_commands import (
    cmd_snapshot_inspect,
    cmd_snapshot_restore,
    cmd_snapshot_take,
)


def _make_manager(secrets=None):
    secrets = secrets or {"DB_URL": "postgres://localhost"}
    vault = MagicMock()
    vault.list.return_value = list(secrets.keys())
    vault.get.side_effect = lambda k, _pp: secrets[k]
    manager = MagicMock()
    manager._load_vault.return_value = vault
    return manager, vault


class TestCmdSnapshotTake(unittest.TestCase):

    def test_output_file_created(self):
        manager, _ = _make_manager({"FOO": "bar"})
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "snap.json")
            args = SimpleNamespace(env="local", passphrase="pp", output=out, note="")
            result = cmd_snapshot_take(args, manager)
            self.assertTrue(Path(out).exists())

    def test_return_message_contains_env(self):
        manager, _ = _make_manager()
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "snap.json")
            args = SimpleNamespace(env="staging", passphrase="pp", output=out, note="")
            msg = cmd_snapshot_take(args, manager)
            self.assertIn("staging", msg)

    def test_return_message_contains_secret_count(self):
        manager, _ = _make_manager({"A": "1", "B": "2"})
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "snap.json")
            args = SimpleNamespace(env="local", passphrase="pp", output=out, note="")
            msg = cmd_snapshot_take(args, manager)
            self.assertIn("2", msg)


class TestCmdSnapshotRestore(unittest.TestCase):

    def _write_snapshot(self, directory, secrets):
        snap = Snapshot(created_at=time.time(), environment="local", secrets=secrets)
        p = Path(directory) / "snap.json"
        save_snapshot(snap, p)
        return p

    def test_vault_set_called_for_each_secret(self):
        manager, vault = _make_manager()
        with tempfile.TemporaryDirectory() as d:
            p = self._write_snapshot(d, {"X": "1", "Y": "2"})
            args = SimpleNamespace(env="local", passphrase="pp", input=str(p))
            cmd_snapshot_restore(args, manager)
            vault.set.assert_any_call("X", "1", "pp")
            vault.set.assert_any_call("Y", "2", "pp")

    def test_return_message_contains_count(self):
        manager, _ = _make_manager()
        with tempfile.TemporaryDirectory() as d:
            p = self._write_snapshot(d, {"A": "a", "B": "b", "C": "c"})
            args = SimpleNamespace(env="local", passphrase="pp", input=str(p))
            msg = cmd_snapshot_restore(args, manager)
            self.assertIn("3", msg)

    def test_missing_file_raises_system_exit(self):
        manager, _ = _make_manager()
        args = SimpleNamespace(env="local", passphrase="pp", input="/no/such/file.json")
        with self.assertRaises(SystemExit):
            cmd_snapshot_restore(args, manager)


class TestCmdSnapshotInspect(unittest.TestCase):

    def test_output_contains_environment(self):
        snap = Snapshot(created_at=time.time(), environment="production", secrets={"K": "v"})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snap.json"
            save_snapshot(snap, p)
            args = SimpleNamespace(input=str(p))
            out = cmd_snapshot_inspect(args)
            self.assertIn("production", out)

    def test_output_lists_keys(self):
        snap = Snapshot(created_at=time.time(), environment="local", secrets={"SECRET_KEY": "x"})
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snap.json"
            save_snapshot(snap, p)
            args = SimpleNamespace(input=str(p))
            out = cmd_snapshot_inspect(args)
            self.assertIn("SECRET_KEY", out)

    def test_missing_file_raises_system_exit(self):
        args = SimpleNamespace(input="/no/file.json")
        with self.assertRaises(SystemExit):
            cmd_snapshot_inspect(args)


if __name__ == "__main__":
    unittest.main()
