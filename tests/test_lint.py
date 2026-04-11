"""Tests for envoy_cli.lint and envoy_cli.lint_commands."""
from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.lint import (
    LintError,
    LintReport,
    LintWarning,
    lint_vault,
)
from envoy_cli.lint_commands import cmd_lint


def _make_vault(secrets: dict) -> MagicMock:
    vault = MagicMock()
    vault.all.return_value = secrets
    return vault


class TestLintWarning(unittest.TestCase):
    def test_to_dict_contains_key_and_message(self):
        w = LintWarning(key="FOO", message="bar")
        d = w.to_dict()
        self.assertEqual(d["key"], "FOO")
        self.assertEqual(d["message"], "bar")

    def test_from_dict_round_trip(self):
        w = LintWarning(key="X", message="msg")
        self.assertEqual(LintWarning.from_dict(w.to_dict()), w)


class TestLintReport(unittest.TestCase):
    def test_has_warnings_false_when_empty(self):
        self.assertFalse(LintReport().has_warnings)

    def test_has_warnings_true(self):
        r = LintReport(warnings=[LintWarning("K", "m")])
        self.assertTrue(r.has_warnings)

    def test_summary_no_issues(self):
        self.assertEqual(LintReport().summary(), "No issues found.")

    def test_summary_lists_warnings(self):
        r = LintReport(warnings=[LintWarning("API_KEY", "short value")])
        summary = r.summary()
        self.assertIn("1 issue(s)", summary)
        self.assertIn("API_KEY", summary)


class TestLintVault(unittest.TestCase):
    def test_raises_on_non_vault(self):
        with self.assertRaises(LintError):
            lint_vault("not-a-vault")

    def test_clean_vault_no_warnings(self):
        vault = _make_vault({"DATABASE_URL": "postgres://user:pass@host/db"})
        report = lint_vault(vault)
        self.assertFalse(report.has_warnings)

    def test_empty_value_raises_warning(self):
        vault = _make_vault({"FOO": ""})
        report = lint_vault(vault)
        keys = [w.key for w in report.warnings]
        self.assertIn("FOO", keys)

    def test_placeholder_value_raises_warning(self):
        vault = _make_vault({"MY_VAR": "changeme"})
        report = lint_vault(vault)
        self.assertTrue(report.has_warnings)

    def test_short_sensitive_key_raises_warning(self):
        vault = _make_vault({"API_KEY": "abc"})
        report = lint_vault(vault)
        self.assertTrue(report.has_warnings)

    def test_internal_meta_keys_skipped(self):
        vault = _make_vault({"__tags__.FOO": ""})
        report = lint_vault(vault)
        self.assertFalse(report.has_warnings)

    def test_multiple_issues_reported(self):
        vault = _make_vault({"SECRET_TOKEN": "x", "BAR": ""})
        report = lint_vault(vault)
        self.assertGreaterEqual(len(report.warnings), 2)


class TestCmdLint(unittest.TestCase):
    def _args(self, env="test"):
        return argparse.Namespace(env=env, base_url="", api_key="")

    def test_returns_no_issues_string(self):
        vault = _make_vault({"SAFE_VAR": "a_long_enough_value"})
        with patch("envoy_cli.lint_commands.SyncManager") as MockMgr:
            MockMgr.return_value._load_vault.return_value = vault
            result = cmd_lint(self._args())
        self.assertIn("No issues", result)

    def test_raises_lint_error_on_load_failure(self):
        with patch("envoy_cli.lint_commands.SyncManager") as MockMgr:
            MockMgr.return_value._load_vault.side_effect = FileNotFoundError("gone")
            from envoy_cli.lint import LintError
            with self.assertRaises(LintError):
                cmd_lint(self._args())


if __name__ == "__main__":
    unittest.main()
