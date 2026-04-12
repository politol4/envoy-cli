"""Tests for envoy_cli.merge."""

from __future__ import annotations

import tempfile
import os
import unittest

from envoy_cli.vault import Vault
from envoy_cli.merge import MergeError, MergeResult, merge_vaults


def _make_vault(secrets: dict, passphrase: str = "pass") -> Vault:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vault")
    tmp.close()
    v = Vault(tmp.name, passphrase)
    for k, val in secrets.items():
        v.set(k, val)
    v.save()
    return v


class TestMergeResult(unittest.TestCase):
    def test_has_changes_true_when_added(self):
        r = MergeResult(added=["A"], overwritten=[], skipped=[])
        self.assertTrue(r.has_changes)

    def test_has_changes_true_when_overwritten(self):
        r = MergeResult(added=[], overwritten=["B"], skipped=[])
        self.assertTrue(r.has_changes)

    def test_has_changes_false_when_only_skipped(self):
        r = MergeResult(added=[], overwritten=[], skipped=["C"])
        self.assertFalse(r.has_changes)

    def test_summary_no_changes(self):
        r = MergeResult(added=[], overwritten=[], skipped=[])
        self.assertEqual(r.summary(), "no changes")

    def test_summary_contains_added_count(self):
        r = MergeResult(added=["X", "Y"], overwritten=[], skipped=[])
        self.assertIn("2 added", r.summary())

    def test_summary_contains_skipped_count(self):
        r = MergeResult(added=[], overwritten=[], skipped=["Z"])
        self.assertIn("1 skipped", r.summary())


class TestMergeVaults(unittest.TestCase):
    def setUp(self):
        self.src = _make_vault({"A": "1", "B": "2"})
        self.dst = _make_vault({"B": "old", "C": "3"})

    def tearDown(self):
        for v in (self.src, self.dst):
            try:
                os.unlink(v.path)
            except FileNotFoundError:
                pass

    def test_returns_merge_result(self):
        result = merge_vaults(self.src, self.dst)
        self.assertIsInstance(result, MergeResult)

    def test_new_key_added_to_dst(self):
        merge_vaults(self.src, self.dst)
        self.assertEqual(self.dst.get("A"), "1")

    def test_existing_key_skipped_by_default(self):
        merge_vaults(self.src, self.dst)
        self.assertEqual(self.dst.get("B"), "old")

    def test_existing_key_overwritten_when_flag_set(self):
        merge_vaults(self.src, self.dst, overwrite=True)
        self.assertEqual(self.dst.get("B"), "2")

    def test_skipped_list_populated(self):
        result = merge_vaults(self.src, self.dst)
        self.assertIn("B", result.skipped)

    def test_added_list_populated(self):
        result = merge_vaults(self.src, self.dst)
        self.assertIn("A", result.added)

    def test_overwritten_list_populated(self):
        result = merge_vaults(self.src, self.dst, overwrite=True)
        self.assertIn("B", result.overwritten)

    def test_prefix_filter_limits_merge(self):
        src = _make_vault({"APP_KEY": "v1", "DB_KEY": "v2"})
        dst = _make_vault({})
        try:
            result = merge_vaults(src, dst, prefix="APP_")
            self.assertIn("APP_KEY", result.added)
            self.assertNotIn("DB_KEY", result.added)
            self.assertIsNone(dst.get("DB_KEY"))
        finally:
            os.unlink(src.path)
            os.unlink(dst.path)

    def test_dst_untouched_key_preserved(self):
        merge_vaults(self.src, self.dst)
        self.assertEqual(self.dst.get("C"), "3")
