"""Tests for crypto and vault modules."""

import pytest
from pathlib import Path

from envoy_cli.crypto import encrypt, decrypt
from envoy_cli.vault import Vault


# ---------------------------------------------------------------------------
# crypto tests
# ---------------------------------------------------------------------------

class TestCrypto:
    PASSPHRASE = "super-secret-passphrase"

    def test_encrypt_returns_string(self):
        result = encrypt("hello", self.PASSPHRASE)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_round_trip(self):
        plaintext = "DATABASE_URL=postgres://localhost/mydb"
        ciphertext = encrypt(plaintext, self.PASSPHRASE)
        assert decrypt(ciphertext, self.PASSPHRASE) == plaintext

    def test_different_ciphertexts_same_input(self):
        """Each call should produce a unique ciphertext (random nonce/salt)."""
        ct1 = encrypt("same", self.PASSPHRASE)
        ct2 = encrypt("same", self.PASSPHRASE)
        assert ct1 != ct2

    def test_wrong_passphrase_raises(self):
        ciphertext = encrypt("secret", self.PASSPHRASE)
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt(ciphertext, "wrong-passphrase")

    def test_invalid_encoding_raises(self):
        with pytest.raises(ValueError):
            decrypt("not-valid-base64!!!", self.PASSPHRASE)


# ---------------------------------------------------------------------------
# vault tests
# ---------------------------------------------------------------------------

class TestVault:
    PASSPHRASE = "vault-pass-123"

    def test_set_and_get(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        vault.set("API_KEY", "abc123")
        assert vault.get("API_KEY") == "abc123"

    def test_get_missing_key_raises(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        with pytest.raises(KeyError):
            vault.get("MISSING")

    def test_delete_key(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        vault.set("TO_DELETE", "value")
        vault.delete("TO_DELETE")
        assert "TO_DELETE" not in vault.list_keys()

    def test_delete_missing_key_raises(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        with pytest.raises(KeyError):
            vault.delete("GHOST")

    def test_persist_and_reload(self, tmp_path):
        path = str(tmp_path / ".envoy_vault")
        vault = Vault(path)
        vault.set("SECRET", "my-secret-value")
        vault.set("DB_URL", "postgres://localhost/test")
        vault.save(self.PASSPHRASE)

        vault2 = Vault(path)
        vault2.load(self.PASSPHRASE)
        assert vault2.get("SECRET") == "my-secret-value"
        assert vault2.get("DB_URL") == "postgres://localhost/test"

    def test_load_empty_vault(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        vault.load(self.PASSPHRASE)  # file does not exist
        assert vault.list_keys() == []

    def test_export(self, tmp_path):
        vault = Vault(str(tmp_path / ".envoy_vault"))
        vault.set("A", "1")
        vault.set("B", "2")
        exported = vault.export()
        assert exported == {"A": "1", "B": "2"}
