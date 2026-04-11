"""Integration tests: access control round-tripped through a real Vault."""
import tempfile
import os
import pytest

from envoy_cli.vault import Vault
from envoy_cli.access import (
    set_access,
    remove_access,
    get_access,
    check_access,
    list_user_keys,
    AccessError,
)


def _make_vault(tmp_path: str, passphrase: str = "integration-pass") -> Vault:
    path = os.path.join(tmp_path, "test.vault")
    v = Vault(path=path, passphrase=passphrase)
    v.secrets = {"DB_URL": "postgres://localhost", "SECRET_KEY": "abc123"}
    v.save()
    return v


class TestAccessIntegration:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.passphrase = "integration-pass"
        self.vault = _make_vault(self.tmp, self.passphrase)

    def _reload(self) -> Vault:
        v = Vault(path=self.vault.path, passphrase=self.passphrase)
        v.load()
        return v

    def test_set_access_persists_across_reload(self):
        self.vault.secrets = set_access(
            self.vault.secrets, "DB_URL", "write", "carol"
        )
        self.vault.save()
        reloaded = self._reload()
        acl = get_access(reloaded.secrets, "DB_URL")
        assert acl.get("carol") == "write"

    def test_remove_access_persists_across_reload(self):
        self.vault.secrets = set_access(
            self.vault.secrets, "DB_URL", "read", "dave"
        )
        self.vault.secrets = remove_access(self.vault.secrets, "DB_URL", "dave")
        self.vault.save()
        reloaded = self._reload()
        acl = get_access(reloaded.secrets, "DB_URL")
        assert "dave" not in acl

    def test_check_access_after_reload(self):
        self.vault.secrets = set_access(
            self.vault.secrets, "SECRET_KEY", "admin", "eve"
        )
        self.vault.save()
        reloaded = self._reload()
        assert check_access(reloaded.secrets, "SECRET_KEY", "eve", "write") is True
        assert check_access(reloaded.secrets, "SECRET_KEY", "eve", "admin") is True

    def test_list_user_keys_after_multiple_grants(self):
        self.vault.secrets = set_access(
            self.vault.secrets, "DB_URL", "read", "frank"
        )
        self.vault.secrets = set_access(
            self.vault.secrets, "SECRET_KEY", "write", "frank"
        )
        self.vault.save()
        reloaded = self._reload()
        keys = list_user_keys(reloaded.secrets, "frank")
        assert "DB_URL" in keys
        assert "SECRET_KEY" in keys

    def test_original_secret_value_unchanged_after_acl_ops(self):
        self.vault.secrets = set_access(
            self.vault.secrets, "DB_URL", "read", "grace"
        )
        self.vault.save()
        reloaded = self._reload()
        assert reloaded.secrets["DB_URL"] == "postgres://localhost"
