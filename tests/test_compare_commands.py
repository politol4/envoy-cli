"""Tests for envoy_cli.compare_commands."""

from __future__ import annotations

import os
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from envoy_cli.compare import CompareError
from envoy_cli.compare_commands import cmd_compare


def _make_args(**kwargs) -> Namespace:
    defaults = {
        "env_a": "local",
        "env_b": "staging",
        "passphrase": "secret",
        "prefix": None,
    }
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestCmdCompare(unittest.TestCase):

    def _patch_load(self, vault_a, vault_b):
        """Patch _load_local_vault to return given vaults in order."""
        return patch(
            "envoy_cli.compare_commands._load_local_vault",
            side_effect=[vault_a, vault_b],
        )

    def _make_vault(self, secrets: dict) -> MagicMock:
        """Create a mock vault whose list() returns (key, value) pairs."""
        v = MagicMock()
        v.list.return_value = list(secrets.items())
        return v

    def test_returns_string(self):
        va = self._make_vault({"K": "v"})
        vb = self._make_vault({"K": "v"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args())
        self.assertIsInstance(result, str)

    def test_identical_envs_message(self):
        va = self._make_vault({"K": "v"})
        vb = self._make_vault({"K": "v"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args())
        self.assertIn("identical", result.lower())

    def test_changed_key_appears_in_output(self):
        va = self._make_vault({"DB_URL": "old"})
        vb = self._make_vault({"DB_URL": "new"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args())
        self.assertIn("DB_URL", result)

    def test_load_failure_raises_compare_error(self):
        with patch(
            "envoy_cli.compare_commands._load_local_vault",
            side_effect=FileNotFoundError("no vault"),
        ):
            with self.assertRaises(CompareError):
                cmd_compare(_make_args())

    def test_env_names_passed_through(self):
        va = self._make_vault({"X": "1"})
        vb = self._make_vault({"X": "2"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args(env_a="dev", env_b="prod"))
        self.assertIn("dev", result)
        self.assertIn("prod", result)

    def test_missing_key_in_env_b_appears_in_output(self):
        """A key present only in env_a should be flagged in the comparison output."""
        va = self._make_vault({"ONLY_IN_A": "value", "SHARED": "same"})
        vb = self._make_vault({"SHARED": "same"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args())
        self.assertIn("ONLY_IN_A", result)

    def test_missing_key_in_env_a_appears_in_output(self):
        """A key present only in env_b should be flagged in the comparison output."""
        va = self._make_vault({"SHARED": "same"})
        vb = self._make_vault({"ONLY_IN_B": "value", "SHARED": "same"})
        with self._patch_load(va, vb):
            result = cmd_compare(_make_args())
        self.assertIn("ONLY_IN_B", result)


if __name__ == "__main__":
    unittest.main()
