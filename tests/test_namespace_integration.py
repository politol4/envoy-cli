"""Integration tests: namespace operations on a real Vault instance."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from envoy_cli.namespace import (
    keys_in_namespace,
    list_namespaces,
    move_namespace,
    namespace_key,
)
from envoy_cli.vault import Vault

PASS = "integration-pass"


def _make_vault(tmp_path: Path, secrets: dict | None = None) -> Vault:
    path = tmp_path / "vault.json"
    v = Vault(str(path), PASS)
    for k, val in (secrets or {}).items():
        v.set(k, val)
    v.save()
    return v


class TestNamespaceIntegration:
    def setup_method(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def teardown_method(self):
        self._tmp.cleanup()

    def test_set_and_list_namespace(self):
        v = _make_vault(self.tmp_path)
        v.set(namespace_key("DB", "HOST"), "localhost")
        v.set(namespace_key("DB", "PORT"), "5432")
        v.set(namespace_key("APP", "DEBUG"), "true")
        v.save()

        reloaded = Vault(str(self.tmp_path / "vault.json"), PASS)
        reloaded.load()
        namespaces = list_namespaces(reloaded.all())
        assert namespaces == ["APP", "DB"]

    def test_keys_in_namespace_after_reload(self):
        v = _make_vault(
            self.tmp_path,
            {"DB.HOST": "localhost", "DB.PORT": "5432", "APP.KEY": "s"},
        )
        reloaded = Vault(str(self.tmp_path / "vault.json"), PASS)
        reloaded.load()
        db_keys = keys_in_namespace(reloaded.all(), "DB")
        assert db_keys == {"HOST": "localhost", "PORT": "5432"}

    def test_move_namespace_persists(self):
        v = _make_vault(
            self.tmp_path,
            {"DB.HOST": "localhost", "DB.PORT": "5432"},
        )
        updated = move_namespace(v.all(), "DB", "PG")
        for k in list(v.all().keys()):
            v.delete(k)
        for k, val in updated.items():
            v.set(k, val)
        v.save()

        reloaded = Vault(str(self.tmp_path / "vault.json"), PASS)
        reloaded.load()
        assert "PG.HOST" in reloaded.all()
        assert "DB.HOST" not in reloaded.all()
