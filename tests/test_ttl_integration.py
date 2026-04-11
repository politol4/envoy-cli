"""Integration tests: TTL operations on a real Vault instance."""

from __future__ import annotations

import time
import unittest

from envoy_cli.ttl import (
    _meta_key,
    get_ttl,
    list_expiring,
    purge_expired,
    remove_ttl,
    set_ttl,
)
from envoy_cli.vault import Vault


def _make_vault(passphrase: str = "integration-pass") -> Vault:
    v = Vault(path="/tmp/ttl_integration_test.vault", passphrase=passphrase)
    v.secrets = {"DB_URL": "postgres://localhost/test", "API_KEY": "abc123"}
    return v


class TestTTLIntegration(unittest.TestCase):
    def setUp(self):
        self.vault = _make_vault()

    def test_set_and_get_round_trip(self):
        self.vault.secrets = set_ttl(self.vault.secrets, "DB_URL", 120)
        remaining = get_ttl(self.vault.secrets, "DB_URL")
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 100)

    def test_remove_clears_ttl(self):
        self.vault.secrets = set_ttl(self.vault.secrets, "API_KEY", 60)
        self.vault.secrets = remove_ttl(self.vault.secrets, "API_KEY")
        self.assertIsNone(get_ttl(self.vault.secrets, "API_KEY"))

    def test_purge_removes_expired_but_keeps_valid(self):
        # Manually inject an already-expired TTL
        self.vault.secrets[_meta_key("DB_URL")] = str(int(time.time()) - 1)
        # Give API_KEY a future TTL
        self.vault.secrets = set_ttl(self.vault.secrets, "API_KEY", 300)
        self.vault.secrets = purge_expired(self.vault.secrets)
        self.assertNotIn("DB_URL", self.vault.secrets)
        self.assertIn("API_KEY", self.vault.secrets)

    def test_list_expiring_only_returns_soon_keys(self):
        self.vault.secrets = set_ttl(self.vault.secrets, "DB_URL", 30)
        self.vault.secrets = set_ttl(self.vault.secrets, "API_KEY", 7200)
        expiring = list_expiring(self.vault.secrets, within_seconds=60)
        self.assertIn("DB_URL", expiring)
        self.assertNotIn("API_KEY", expiring)

    def test_purge_preserves_keys_without_ttl(self):
        self.vault.secrets = purge_expired(self.vault.secrets)
        self.assertIn("DB_URL", self.vault.secrets)
        self.assertIn("API_KEY", self.vault.secrets)

    def test_meta_keys_not_included_in_list_expiring(self):
        self.vault.secrets = set_ttl(self.vault.secrets, "DB_URL", 10)
        expiring = list_expiring(self.vault.secrets, within_seconds=60)
        for key in expiring:
            self.assertFalse(key.startswith("__ttl__"), f"Meta key leaked: {key}")
