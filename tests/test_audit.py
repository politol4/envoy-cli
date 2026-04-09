"""Tests for envoy_cli.audit module."""

import os
import tempfile
import unittest

from envoy_cli.audit import AuditEntry, AuditLog


class TestAuditEntry(unittest.TestCase):
    def test_to_dict_contains_required_fields(self):
        entry = AuditEntry(action="set", key="DB_URL", environment="staging", user="alice")
        d = entry.to_dict()
        self.assertEqual(d["action"], "set")
        self.assertEqual(d["key"], "DB_URL")
        self.assertEqual(d["environment"], "staging")
        self.assertEqual(d["user"], "alice")
        self.assertIn("timestamp", d)
        self.assertIn("version", d)

    def test_from_dict_round_trip(self):
        entry = AuditEntry(action="delete", key="SECRET", environment="production", user="bob")
        restored = AuditEntry.from_dict(entry.to_dict())
        self.assertEqual(restored.action, "delete")
        self.assertEqual(restored.key, "SECRET")
        self.assertEqual(restored.environment, "production")
        self.assertEqual(restored.user, "bob")
        self.assertEqual(restored.timestamp, entry.timestamp)


class TestAuditLog(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.tmp_dir, "audit.log")
        self.log = AuditLog(self.log_path)

    def tearDown(self):
        self.log.clear()

    def test_record_creates_file(self):
        self.log.record("set", "API_KEY", "local")
        self.assertTrue(os.path.exists(self.log_path))

    def test_record_returns_entry(self):
        entry = self.log.record("get", "TOKEN", "staging", user="carol")
        self.assertIsInstance(entry, AuditEntry)
        self.assertEqual(entry.action, "get")
        self.assertEqual(entry.user, "carol")

    def test_history_returns_all_entries(self):
        self.log.record("set", "A", "local")
        self.log.record("set", "B", "staging")
        entries = self.log.history()
        self.assertEqual(len(entries), 2)

    def test_history_filters_by_environment(self):
        self.log.record("set", "A", "local")
        self.log.record("set", "B", "staging")
        self.log.record("push", "B", "staging")
        entries = self.log.history(environment="staging")
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e.environment == "staging" for e in entries))

    def test_history_filters_by_key(self):
        self.log.record("set", "DB_URL", "local")
        self.log.record("set", "API_KEY", "local")
        self.log.record("get", "DB_URL", "production")
        entries = self.log.history(key="DB_URL")
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e.key == "DB_URL" for e in entries))

    def test_history_empty_when_no_log(self):
        entries = self.log.history()
        self.assertEqual(entries, [])

    def test_clear_removes_log_file(self):
        self.log.record("set", "X", "local")
        self.log.clear()
        self.assertFalse(os.path.exists(self.log_path))

    def test_multiple_records_persisted(self):
        for i in range(5):
            self.log.record("set", f"KEY_{i}", "local")
        entries = self.log.history()
        self.assertEqual(len(entries), 5)


if __name__ == "__main__":
    unittest.main()
