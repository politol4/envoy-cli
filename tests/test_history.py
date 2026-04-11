"""Tests for envoy_cli.history."""
import os
import tempfile
import time
import unittest

from envoy_cli.history import History, HistoryEntry, HistoryError


class TestHistoryEntry(unittest.TestCase):
    def _make_entry(self, **kwargs):
        defaults = dict(action="set", key="DB_URL", env="staging")
        defaults.update(kwargs)
        return HistoryEntry(**defaults)

    def test_to_dict_contains_required_fields(self):
        e = self._make_entry()
        d = e.to_dict()
        for field in ("action", "key", "env", "timestamp", "actor", "note"):
            self.assertIn(field, d)

    def test_from_dict_round_trip(self):
        e = self._make_entry(note="initial set")
        e2 = HistoryEntry.from_dict(e.to_dict())
        self.assertEqual(e.action, e2.action)
        self.assertEqual(e.key, e2.key)
        self.assertEqual(e.note, e2.note)

    def test_from_dict_missing_field_raises(self):
        with self.assertRaises(HistoryError):
            HistoryEntry.from_dict({"action": "set", "key": "X"})

    def test_defaults_actor_and_note(self):
        e = HistoryEntry.from_dict({"action": "delete", "key": "X", "env": "prod", "timestamp": 1.0})
        self.assertEqual(e.actor, "local")
        self.assertEqual(e.note, "")


class TestHistory(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._path = os.path.join(self._tmp, "history.jsonl")

    def tearDown(self):
        if os.path.exists(self._path):
            os.remove(self._path)
        os.rmdir(self._tmp)

    def _history(self):
        return History(self._path)

    def test_entries_empty_when_no_file(self):
        self.assertEqual(self._history().entries(), [])

    def test_record_and_retrieve(self):
        h = self._history()
        h.record(HistoryEntry(action="set", key="FOO", env="dev"))
        entries = h.entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].key, "FOO")

    def test_filter_by_env(self):
        h = self._history()
        h.record(HistoryEntry(action="set", key="A", env="dev"))
        h.record(HistoryEntry(action="set", key="B", env="prod"))
        self.assertEqual(len(h.entries(env="dev")), 1)
        self.assertEqual(h.entries(env="dev")[0].key, "A")

    def test_filter_by_key(self):
        h = self._history()
        h.record(HistoryEntry(action="set", key="X", env="dev"))
        h.record(HistoryEntry(action="set", key="Y", env="dev"))
        self.assertEqual(len(h.entries(key="X")), 1)

    def test_clear_returns_count(self):
        h = self._history()
        h.record(HistoryEntry(action="set", key="A", env="dev"))
        h.record(HistoryEntry(action="delete", key="B", env="dev"))
        self.assertEqual(h.clear(), 2)

    def test_clear_removes_file(self):
        h = self._history()
        h.record(HistoryEntry(action="set", key="A", env="dev"))
        h.clear()
        self.assertFalse(os.path.exists(self._path))

    def test_multiple_records_ordered(self):
        h = self._history()
        for i in range(3):
            h.record(HistoryEntry(action="set", key=f"K{i}", env="dev", timestamp=float(i)))
        keys = [e.key for e in h.entries()]
        self.assertEqual(keys, ["K0", "K1", "K2"])
