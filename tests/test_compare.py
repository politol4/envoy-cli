"""Tests for envoy_cli.compare."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from envoy_cli.compare import CompareReport, compare_vaults
from envoy_cli.diff import DiffResult


def _make_vault(secrets: dict) -> MagicMock:
    vault = MagicMock()
    vault.list.return_value = list(secrets.items())
    return vault


class TestCompareVaults(unittest.TestCase):

    def test_returns_compare_report(self):
        va = _make_vault({"KEY": "val"})
        vb = _make_vault({"KEY": "val"})
        report = compare_vaults(va, vb, env_a="local", env_b="staging")
        self.assertIsInstance(report, CompareReport)

    def test_no_changes_when_identical(self):
        va = _make_vault({"A": "1", "B": "2"})
        vb = _make_vault({"A": "1", "B": "2"})
        report = compare_vaults(va, vb)
        self.assertFalse(report.has_changes)

    def test_detects_added_key(self):
        va = _make_vault({"A": "1"})
        vb = _make_vault({"A": "1", "B": "2"})
        report = compare_vaults(va, vb)
        self.assertTrue(report.has_changes)
        self.assertIn("B", report.diff.added)

    def test_detects_removed_key(self):
        va = _make_vault({"A": "1", "B": "2"})
        vb = _make_vault({"A": "1"})
        report = compare_vaults(va, vb)
        self.assertIn("B", report.diff.removed)

    def test_detects_changed_value(self):
        va = _make_vault({"A": "old"})
        vb = _make_vault({"A": "new"})
        report = compare_vaults(va, vb)
        self.assertIn("A", report.diff.changed)

    def test_prefix_filter_applied(self):
        va = _make_vault({"APP_KEY": "1", "OTHER": "x"})
        vb = _make_vault({"APP_KEY": "1", "OTHER": "y"})
        report = compare_vaults(va, vb, prefix="APP_")
        self.assertFalse(report.has_changes)

    def test_warning_when_env_empty(self):
        va = _make_vault({})
        vb = _make_vault({"A": "1"})
        report = compare_vaults(va, vb, env_a="empty", env_b="full")
        self.assertTrue(any("empty" in w for w in report.warnings))

    def test_env_names_in_report(self):
        va = _make_vault({"X": "1"})
        vb = _make_vault({"X": "1"})
        report = compare_vaults(va, vb, env_a="local", env_b="prod")
        self.assertEqual(report.env_a, "local")
        self.assertEqual(report.env_b, "prod")

    def test_summary_contains_env_names(self):
        va = _make_vault({"X": "1"})
        vb = _make_vault({"X": "2"})
        report = compare_vaults(va, vb, env_a="dev", env_b="staging")
        summary = report.summary()
        self.assertIn("dev", summary)
        self.assertIn("staging", summary)

    def test_summary_identical_message(self):
        va = _make_vault({"K": "v"})
        vb = _make_vault({"K": "v"})
        report = compare_vaults(va, vb)
        self.assertIn("identical", report.summary().lower())


if __name__ == "__main__":
    unittest.main()
