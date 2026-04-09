"""Unit tests for envoy_cli.sync.SyncManager."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


PASSPHRASE = "sync-test-pass"


class TestSyncManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mock_client = MagicMock()
        self.manager = SyncManager(self.mock_client, vault_dir=self.tmp)

    def _make_vault(self, profile: str, data: dict) -> str:
        vault = Vault(self.manager._vault_path(profile), PASSPHRASE)
        for k, v in data.items():
            vault.set(k, v)
        vault.save()
        return self.manager._vault_path(profile)

    # ------------------------------------------------------------------
    # push
    # ------------------------------------------------------------------

    def test_push_calls_client_push(self):
        self._make_vault("dev", {"KEY": "value"})
        self.manager.push("dev", PASSPHRASE)
        self.mock_client.push.assert_called_once()
        call_profile = self.mock_client.push.call_args[0][0]
        self.assertEqual(call_profile, "dev")

    def test_push_sends_non_empty_ciphertext(self):
        self._make_vault("dev", {"SECRET": "abc123"})
        self.manager.push("dev", PASSPHRASE)
        ciphertext = self.mock_client.push.call_args[0][1]
        self.assertIsInstance(ciphertext, str)
        self.assertGreater(len(ciphertext), 0)

    # ------------------------------------------------------------------
    # pull
    # ------------------------------------------------------------------

    def test_pull_writes_vault_file(self):
        # First push to capture a valid ciphertext
        self._make_vault("staging", {"DB_URL": "postgres://localhost/db"})
        self.manager.push("staging", PASSPHRASE)
        ciphertext = self.mock_client.push.call_args[0][1]

        # Now simulate pull with that ciphertext
        self.mock_client.pull.return_value = ciphertext
        vault_path = self.manager._vault_path("staging")
        os.remove(vault_path)  # remove so we confirm pull recreates it

        self.manager.pull("staging", PASSPHRASE)
        self.assertTrue(os.path.exists(vault_path))

    # ------------------------------------------------------------------
    # apply
    # ------------------------------------------------------------------

    def test_apply_writes_env_file(self):
        self._make_vault("prod", {"API_KEY": "secret", "PORT": "8080"})
        env_out = os.path.join(self.tmp, ".env")
        self.manager.apply("prod", PASSPHRASE, env_path=env_out)
        self.assertTrue(os.path.exists(env_out))
        content = open(env_out).read()
        self.assertIn("API_KEY", content)
        self.assertIn("PORT", content)

    # ------------------------------------------------------------------
    # import_env
    # ------------------------------------------------------------------

    def test_import_env_populates_vault(self):
        env_in = os.path.join(self.tmp, ".env")
        with open(env_in, "w") as f:
            f.write("IMPORTED_KEY=hello\nANOTHER=world\n")

        self.manager.import_env("local", PASSPHRASE, env_path=env_in)
        vault = Vault(self.manager._vault_path("local"), PASSPHRASE)
        vault.load()
        self.assertEqual(vault.get("IMPORTED_KEY"), "hello")
        self.assertEqual(vault.get("ANOTHER"), "world")
