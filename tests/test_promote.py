"""Tests for envoy_cli.promote."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from envoy_cli.promote import PromoteError, PromoteResult, promote_env
from envoy_cli.vault import Vault


PASSPHRASE = "test-passphrase"


def _make_vault(secrets: dict) -> Vault:
    v = Vault.__new__(Vault)
    v._secrets = dict(secrets)
    return v


def _make_manager(vaults: dict):
    """Return a SyncManager-like mock backed by *vaults* dict."""
    manager = MagicMock()

    def _load(env, passphrase):
        if env not in vaults:
            vaults[env] = _make_vault({})
        return vaults[env]

    def _save(env, vault, passphrase):
        vaults[env] = vault

    manager._load_vault.side_effect = _load
    manager._save_vault.side_effect = _save
    return manager


class TestPromoteResult(unittest.TestCase):
    def _result(self, promoted=None, skipped=None):
        return PromoteResult(
            src_env="staging",
            dst_env="production",
            promoted=promoted or [],
            skipped=skipped or [],
        )

    def test_has_changes_true_when_promoted(self):
        r = self._result(promoted=["KEY"])
        self.assertTrue(r.has_changes)

    def test_has_changes_false_when_empty(self):
        r = self._result()
        self.assertFalse(r.has_changes)

    def test_summary_contains_env_names(self):
        r = self._result(promoted=["A", "B"], skipped=["C"])
        s = r.summary()
        self.assertIn("staging", s)
        self.assertIn("production", s)

    def test_summary_contains_counts(self):
        r = self._result(promoted=["A", "B"], skipped=["C"])
        s = r.summary()
        self.assertIn("2", s)
        self.assertIn("1", s)


class TestPromoteEnv(unittest.TestCase):
    def setUp(self):
        self.vaults = {
            "staging": _make_vault({"DB_URL": "postgres://staging", "API_KEY": "abc"}),
            "production": _make_vault({"DB_URL": "postgres://prod"}),
        }
        self.manager = _make_manager(self.vaults)

    def test_same_env_raises(self):
        with self.assertRaises(PromoteError):
            promote_env(self.manager, "staging", "staging", PASSPHRASE)

    def test_all_keys_promoted_by_default(self):
        result = promote_env(self.manager, "staging", "production", PASSPHRASE)
        self.assertIn("API_KEY", result.promoted)
        self.assertIn("DB_URL", result.promoted)

    def test_overwrite_false_skips_existing_key(self):
        result = promote_env(
            self.manager, "staging", "production", PASSPHRASE, overwrite=False
        )
        self.assertIn("DB_URL", result.skipped)
        self.assertIn("API_KEY", result.promoted)

    def test_key_filter_restricts_promotion(self):
        result = promote_env(
            self.manager, "staging", "production", PASSPHRASE, keys=["API_KEY"]
        )
        self.assertEqual(result.promoted, ["API_KEY"])

    def test_missing_key_raises(self):
        with self.assertRaises(PromoteError):
            promote_env(
                self.manager, "staging", "production", PASSPHRASE, keys=["MISSING"]
            )

    def test_destination_vault_saved(self):
        promote_env(self.manager, "staging", "production", PASSPHRASE)
        self.manager._save_vault.assert_called_once()

    def test_promoted_keys_present_in_dst_vault(self):
        promote_env(self.manager, "staging", "production", PASSPHRASE)
        dst = self.vaults["production"]
        self.assertEqual(dst._secrets.get("API_KEY"), "abc")
