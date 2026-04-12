"""Tests for envoy_cli.cascade and envoy_cli.cascade_commands."""

from __future__ import annotations

import os
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import MagicMock

from envoy_cli.cascade import CascadeError, CascadeResult, cascade
from envoy_cli.cascade_commands import cmd_cascade
from envoy_cli.vault import Vault

PASS = "test-pass"


def _make_vault(secrets: dict, tmp_dir: str, name: str = "vault.enc") -> Vault:
    path = os.path.join(tmp_dir, name)
    v = Vault(path)
    v.load(PASS)  # initialise empty vault
    for k, val in secrets.items():
        v.set(k, val, PASS)
    v.save(PASS)
    return v


class TestCascadeResult(unittest.TestCase):
    def test_has_changes_true_when_added(self):
        r = CascadeResult(added=["A"], skipped=[])
        self.assertTrue(r.has_changes)

    def test_has_changes_false_when_only_skipped(self):
        r = CascadeResult(added=[], skipped=["A"])
        self.assertFalse(r.has_changes)

    def test_summary_no_changes(self):
        r = CascadeResult()
        self.assertEqual(r.summary(), "no changes")

    def test_summary_with_added_and_skipped(self):
        r = CascadeResult(added=["A", "B"], skipped=["C"])
        self.assertIn("2 key(s) added", r.summary())
        self.assertIn("1 key(s) skipped", r.summary())

    def test_as_lines_prefix_plus_for_added(self):
        r = CascadeResult(added=["FOO"], skipped=[])
        self.assertTrue(any(line.startswith("  +") for line in r.as_lines()))

    def test_as_lines_prefix_tilde_for_skipped(self):
        r = CascadeResult(added=[], skipped=["BAR"])
        self.assertTrue(any(line.startswith("  ~") for line in r.as_lines()))


class TestCascade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_empty_source_raises(self):
        target = _make_vault({}, self.tmp, "target.enc")
        with self.assertRaises(CascadeError):
            cascade({}, target, PASS)

    def test_missing_keys_are_added(self):
        source = {"A": "1", "B": "2"}
        target = _make_vault({}, self.tmp, "target.enc")
        result = cascade(source, target, PASS)
        self.assertIn("A", result.added)
        self.assertIn("B", result.added)

    def test_existing_keys_are_skipped(self):
        source = {"A": "src_val"}
        target = _make_vault({"A": "target_val"}, self.tmp, "target.enc")
        result = cascade(source, target, PASS)
        self.assertIn("A", result.skipped)
        self.assertEqual(target.get("A", PASS), "target_val")

    def test_prefix_filter_applied(self):
        source = {"APP_KEY": "1", "DB_HOST": "2"}
        target = _make_vault({}, self.tmp, "target.enc")
        result = cascade(source, target, PASS, prefix="APP_")
        self.assertIn("APP_KEY", result.added)
        self.assertNotIn("DB_HOST", result.added)
        self.assertNotIn("DB_HOST", result.skipped)


class TestCmdCascade(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _args(self, **kwargs) -> Namespace:
        defaults = dict(
            source_file="src.enc",
            source_passphrase=PASS,
            target_file="tgt.enc",
            target_passphrase=PASS,
            prefix="",
        )
        defaults.update(kwargs)
        return Namespace(**defaults)

    def test_returns_string_with_summary(self):
        src = _make_vault({"X": "1"}, self.tmp, "src.enc")
        tgt = _make_vault({}, self.tmp, "tgt.enc")
        args = self._args()
        result = cmd_cascade(args, source_vault=src, target_vault=tgt)
        self.assertIsInstance(result, str)
        self.assertIn("Cascade complete", result)

    def test_added_key_visible_in_output(self):
        src = _make_vault({"NEW_KEY": "val"}, self.tmp, "src.enc")
        tgt = _make_vault({}, self.tmp, "tgt.enc")
        result = cmd_cascade(self._args(), source_vault=src, target_vault=tgt)
        self.assertIn("NEW_KEY", result)

    def test_no_changes_message_when_all_present(self):
        src = _make_vault({"A": "1"}, self.tmp, "src.enc")
        tgt = _make_vault({"A": "2"}, self.tmp, "tgt.enc")
        result = cmd_cascade(self._args(), source_vault=src, target_vault=tgt)
        self.assertIn("no changes", result)


if __name__ == "__main__":
    unittest.main()
