"""Tests for envoy_cli.namespace_commands."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from envoy_cli.namespace_commands import (
    cmd_namespace_delete,
    cmd_namespace_list,
    cmd_namespace_move,
    cmd_namespace_set,
    cmd_namespace_show,
)


def _make_args(**kwargs):
    defaults = dict(env="development", passphrase="secret")
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_vault(secrets: dict):
    vault = MagicMock()
    store = dict(secrets)
    vault.all.return_value = store
    vault.set.side_effect = lambda k, v: store.update({k: v})
    vault.delete.side_effect = lambda k: store.pop(k, None)
    return vault


def _patch_manager(vault):
    mgr = MagicMock()
    mgr._load_vault.return_value = vault
    return patch("envoy_cli.namespace_commands._make_manager", return_value=mgr)


class TestCmdNamespaceList:
    def test_returns_sorted_namespaces(self):
        vault = _make_vault({"DB.HOST": "h", "APP.KEY": "k"})
        with _patch_manager(vault):
            result = cmd_namespace_list(_make_args())
        assert "APP" in result
        assert "DB" in result

    def test_no_namespaces_message(self):
        vault = _make_vault({"HOST": "h"})
        with _patch_manager(vault):
            result = cmd_namespace_list(_make_args())
        assert "No namespaces" in result


class TestCmdNamespaceShow:
    def test_shows_bare_keys(self):
        vault = _make_vault({"DB.HOST": "localhost", "DB.PORT": "5432"})
        with _patch_manager(vault):
            result = cmd_namespace_show(_make_args(namespace="DB"))
        assert "HOST" in result
        assert "PORT" in result

    def test_empty_namespace_message(self):
        vault = _make_vault({"DB.HOST": "localhost"})
        with _patch_manager(vault):
            result = cmd_namespace_show(_make_args(namespace="APP"))
        assert "empty" in result or "does not exist" in result


class TestCmdNamespaceSet:
    def test_sets_namespaced_key(self):
        vault = _make_vault({})
        with _patch_manager(vault):
            result = cmd_namespace_set(_make_args(namespace="DB", key="HOST", value="localhost"))
        vault.set.assert_called_once_with("DB.HOST", "localhost")
        assert "DB.HOST" in result

    def test_saves_vault(self):
        vault = _make_vault({})
        with _patch_manager(vault):
            cmd_namespace_set(_make_args(namespace="DB", key="HOST", value="localhost"))
        vault.save.assert_called_once()


class TestCmdNamespaceDelete:
    def test_deletes_namespaced_key(self):
        vault = _make_vault({"DB.HOST": "localhost"})
        with _patch_manager(vault):
            result = cmd_namespace_delete(_make_args(namespace="DB", key="HOST"))
        vault.delete.assert_called_once_with("DB.HOST")
        assert "DB.HOST" in result


class TestCmdNamespaceMove:
    def test_moves_keys_to_new_namespace(self):
        vault = _make_vault({"DB.HOST": "localhost", "DB.PORT": "5432"})
        with _patch_manager(vault):
            result = cmd_namespace_move(_make_args(src="DB", dst="PG"))
        assert "PG" in result
        assert "2" in result

    def test_saves_vault_after_move(self):
        vault = _make_vault({"DB.HOST": "localhost"})
        with _patch_manager(vault):
            cmd_namespace_move(_make_args(src="DB", dst="PG"))
        vault.save.assert_called_once()
