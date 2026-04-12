"""Tests for envoy_cli.rollback."""

from __future__ import annotations

import os
import json
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from envoy_cli.snapshot import Snapshot
from envoy_cli.rollback import (
    RollbackError,
    list_snapshots,
    rollback_to_index,
    rollback_to_label,
)


def _make_snapshot(env: str, secrets: dict, label: str = "") -> Snapshot:
    return Snapshot(
        env=env,
        label=label,
        timestamp=datetime.now(timezone.utc).isoformat(),
        secrets=secrets,
    )


def _make_vault(initial: dict | None = None) -> MagicMock:
    store: dict = dict(initial or {})

    vault = MagicMock()
    vault.all.side_effect = lambda: dict(store)
    vault.set.side_effect = lambda k, v: store.update({k: v})
    vault.delete.side_effect = lambda k: store.pop(k, None)
    vault._store = store
    return vault


class TestListSnapshots(unittest.TestCase):
    def test_empty_dir_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as d:
            result = list_snapshots(d, "production")
        self.assertEqual(result, [])

    def test_nonexistent_dir_returns_empty_list(self):
        result = list_snapshots("/nonexistent/path/xyz", "production")
        self.assertEqual(result, [])

    def test_returns_only_matching_env(self):
        with tempfile.TemporaryDirectory() as d:
            for env, label in [("production", "snap-a"), ("staging", "snap-b")]:
                snap = _make_snapshot(env, {"K": "V"}, label)
                path = os.path.join(d, f"{label}.json")
                with open(path, "w") as fh:
                    json.dump(snap.to_dict(), fh)
            result = list_snapshots(d, "production")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, "snap-a")

    def test_ignores_non_json_files(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "readme.txt"), "w").close()
            result = list_snapshots(d, "production")
        self.assertEqual(result, [])


class TestRollbackToIndex(unittest.TestCase):
    def setUp(self):
        self.snap_a = _make_snapshot("production", {"A": "1", "B": "2"}, "v1")
        self.snap_b = _make_snapshot("production", {"A": "99"}, "v2")
        self.snapshots = [self.snap_a, self.snap_b]

    def test_empty_snapshots_raises(self):
        vault = _make_vault()
        with self.assertRaises(RollbackError):
            rollback_to_index(vault, [], 0)

    def test_out_of_range_index_raises(self):
        vault = _make_vault()
        with self.assertRaises(RollbackError):
            rollback_to_index(vault, self.snapshots, 5)

    def test_negative_index_raises(self):
        vault = _make_vault()
        with self.assertRaises(RollbackError):
            rollback_to_index(vault, self.snapshots, -1)

    def test_restores_correct_secrets(self):
        vault = _make_vault({"OLD": "gone"})
        count = rollback_to_index(vault, self.snapshots, 0)
        self.assertEqual(count, 2)
        self.assertIn(("A", "1"), vault._store.items())
        self.assertIn(("B", "2"), vault._store.items())
        self.assertNotIn("OLD", vault._store)

    def test_vault_save_called(self):
        vault = _make_vault()
        rollback_to_index(vault, self.snapshots, 1)
        vault.save.assert_called_once()


class TestRollbackToLabel(unittest.TestCase):
    def setUp(self):
        self.snaps = [
            _make_snapshot("production", {"X": "1"}, "alpha"),
            _make_snapshot("production", {"X": "2"}, "beta"),
            _make_snapshot("production", {"X": "3"}, "alpha"),  # duplicate label
        ]

    def test_unknown_label_raises(self):
        vault = _make_vault()
        with self.assertRaises(RollbackError):
            rollback_to_label(vault, self.snaps, "gamma")

    def test_most_recent_label_used(self):
        vault = _make_vault()
        count = rollback_to_label(vault, self.snaps, "alpha")
        # Most recent "alpha" has X=3
        self.assertEqual(count, 1)
        self.assertEqual(vault._store.get("X"), "3")

    def test_unique_label_restored(self):
        vault = _make_vault()
        rollback_to_label(vault, self.snaps, "beta")
        self.assertEqual(vault._store.get("X"), "2")
