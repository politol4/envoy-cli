"""Tests for envoy_cli.snapshot."""
import json
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from envoy_cli.snapshot import (
    Snapshot,
    SnapshotError,
    load_snapshot,
    restore_snapshot,
    save_snapshot,
    take_snapshot,
)


def _make_vault(secrets: dict):
    vault = MagicMock()
    vault.list.return_value = list(secrets.keys())
    vault.get.side_effect = lambda k, _pp: secrets[k]
    return vault


class TestSnapshot(unittest.TestCase):

    def test_to_dict_contains_required_fields(self):
        s = Snapshot(created_at=1.0, environment="prod", secrets={"K": "V"}, note="n")
        d = s.to_dict()
        self.assertIn("created_at", d)
        self.assertIn("environment", d)
        self.assertIn("secrets", d)
        self.assertIn("note", d)

    def test_from_dict_round_trip(self):
        original = Snapshot(created_at=42.0, environment="staging", secrets={"A": "1"}, note="x")
        restored = Snapshot.from_dict(original.to_dict())
        self.assertEqual(original.environment, restored.environment)
        self.assertEqual(original.secrets, restored.secrets)
        self.assertEqual(original.note, restored.note)

    def test_from_dict_missing_key_raises(self):
        with self.assertRaises(KeyError):
            Snapshot.from_dict({"environment": "local"})


class TestTakeSnapshot(unittest.TestCase):

    def test_secrets_captured(self):
        vault = _make_vault({"DB": "postgres", "KEY": "abc"})
        snap = take_snapshot(vault, "pass", "local")
        self.assertEqual(snap.secrets, {"DB": "postgres", "KEY": "abc"})

    def test_environment_stored(self):
        vault = _make_vault({})
        snap = take_snapshot(vault, "pass", "production", note="before deploy")
        self.assertEqual(snap.environment, "production")
        self.assertEqual(snap.note, "before deploy")

    def test_created_at_is_recent(self):
        vault = _make_vault({})
        before = time.time()
        snap = take_snapshot(vault, "pass", "local")
        after = time.time()
        self.assertGreaterEqual(snap.created_at, before)
        self.assertLessEqual(snap.created_at, after)


class TestRestoreSnapshot(unittest.TestCase):

    def test_all_secrets_written(self):
        snap = Snapshot(created_at=1.0, environment="local", secrets={"A": "1", "B": "2"})
        vault = MagicMock()
        count = restore_snapshot(snap, vault, "pass")
        self.assertEqual(count, 2)
        vault.set.assert_any_call("A", "1", "pass")
        vault.set.assert_any_call("B", "2", "pass")

    def test_returns_secret_count(self):
        snap = Snapshot(created_at=1.0, environment="local", secrets={"X": "y"})
        vault = MagicMock()
        self.assertEqual(restore_snapshot(snap, vault, "p"), 1)


class TestSaveLoadSnapshot(unittest.TestCase):

    def test_save_and_load_round_trip(self, tmp_path=None):
        import tempfile, os
        snap = Snapshot(created_at=99.0, environment="staging", secrets={"S": "v"}, note="t")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "snap.json"
            save_snapshot(snap, p)
            loaded = load_snapshot(p)
        self.assertEqual(loaded.secrets, snap.secrets)
        self.assertEqual(loaded.environment, snap.environment)

    def test_load_missing_file_raises(self):
        with self.assertRaises(SnapshotError):
            load_snapshot(Path("/nonexistent/snap.json"))

    def test_load_invalid_json_raises(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text("not json", encoding="utf-8")
            with self.assertRaises(SnapshotError):
                load_snapshot(p)


if __name__ == "__main__":
    unittest.main()
