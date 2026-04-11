"""Integration tests: pin interacts correctly with vault secrets."""

import tempfile
import os

import pytest

from envoy_cli.pin import (
    PinError,
    filter_unpinned,
    is_pinned,
    list_pinned,
    pin_key,
    unpin_key,
)
from envoy_cli.vault import Vault


def _make_vault(tmp_path: str, secrets: dict, passphrase: str = "test-pass") -> Vault:
    path = os.path.join(tmp_path, "vault.enc")
    v = Vault(path)
    v.secrets = secrets
    v.save(passphrase)
    return v


class TestPinIntegration:
    def setup_method(self):
        self._tmp = tempfile.mkdtemp()

    def test_pin_persists_across_vault_reload(self):
        path = os.path.join(self._tmp, "vault.enc")
        v = Vault(path)
        v.secrets = {"DB": "postgres"}
        v.secrets = pin_key(v.secrets, "DB")
        v.save("pass")

        v2 = Vault(path)
        v2.load("pass")
        assert is_pinned(v2.secrets, "DB")

    def test_unpin_persists_across_vault_reload(self):
        path = os.path.join(self._tmp, "vault.enc")
        v = Vault(path)
        v.secrets = pin_key({"DB": "postgres"}, "DB")
        v.secrets = unpin_key(v.secrets, "DB")
        v.save("pass")

        v2 = Vault(path)
        v2.load("pass")
        assert not is_pinned(v2.secrets, "DB")

    def test_filter_unpinned_prevents_overwrite(self):
        current = pin_key({"DB": "old", "TOKEN": "t"}, "DB")
        incoming = {"DB": "new", "TOKEN": "new_token"}
        safe = filter_unpinned(incoming, current)
        assert safe.get("DB") is None
        assert safe["TOKEN"] == "new_token"

    def test_list_pinned_excludes_meta_entries(self):
        secrets = pin_key(pin_key({"A": "1", "B": "2"}, "A"), "B")
        pinned = list_pinned(secrets)
        assert pinned == ["A", "B"]
        assert len(pinned) == 2

    def test_pin_then_delete_key_leaves_orphan_meta(self):
        """Deleting a key without unpinning leaves an orphan meta key — expected behaviour."""
        secrets = pin_key({"X": "val"}, "X")
        del secrets["X"]
        # meta key still present but list_pinned skips keys not in secrets
        pinned = list_pinned(secrets)
        assert "X" not in pinned
