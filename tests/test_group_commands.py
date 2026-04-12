"""Tests for envoy_cli.group_commands."""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest

from envoy_cli.group import GROUP_PREFIX, GroupError
from envoy_cli.group_commands import (
    cmd_group_create,
    cmd_group_delete,
    cmd_group_export,
    cmd_group_list,
    cmd_group_show,
)


def _make_args(**kwargs) -> types.SimpleNamespace:
    defaults = {"env": "dev", "passphrase": "pass", "vault_dir": "."}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _make_manager(secrets: dict):
    vault = MagicMock()
    vault.secrets = secrets
    mgr = MagicMock()
    mgr._load_vault.return_value = vault
    mgr._save_vault = MagicMock()
    return mgr, vault


def _patch(secrets: dict):
    mgr, vault = _make_manager(secrets)
    return patch("envoy_cli.group_commands._make_manager", return_value=mgr), mgr, vault


class TestCmdGroupCreate:
    def test_returns_confirmation(self):
        patcher, mgr, vault = _patch({"DB_HOST": "localhost"})
        with patcher:
            result = cmd_group_create(_make_args(group="db", keys="DB_HOST"))
        assert "db" in result
        assert "1" in result

    def test_vault_saved_after_create(self):
        patcher, mgr, vault = _patch({"DB_HOST": "localhost"})
        with patcher:
            cmd_group_create(_make_args(group="db", keys="DB_HOST"))
        mgr._save_vault.assert_called_once()

    def test_meta_key_written_to_vault(self):
        patcher, mgr, vault = _patch({"A": "1", "B": "2"})
        with patcher:
            cmd_group_create(_make_args(group="mygroup", keys="A,B"))
        assert f"{GROUP_PREFIX}mygroup" in vault.secrets


class TestCmdGroupDelete:
    def test_returns_confirmation(self):
        secrets = {"A": "1", f"{GROUP_PREFIX}g": "A"}
        patcher, mgr, vault = _patch(secrets)
        with patcher:
            result = cmd_group_delete(_make_args(group="g"))
        assert "g" in result
        assert "deleted" in result

    def test_vault_saved_after_delete(self):
        secrets = {"A": "1", f"{GROUP_PREFIX}g": "A"}
        patcher, mgr, vault = _patch(secrets)
        with patcher:
            cmd_group_delete(_make_args(group="g"))
        mgr._save_vault.assert_called_once()


class TestCmdGroupList:
    def test_returns_group_names(self):
        secrets = {f"{GROUP_PREFIX}alpha": "A", f"{GROUP_PREFIX}beta": "B"}
        patcher, mgr, vault = _patch(secrets)
        with patcher:
            result = cmd_group_list(_make_args())
        assert "alpha" in result
        assert "beta" in result

    def test_no_groups_returns_message(self):
        patcher, mgr, vault = _patch({})
        with patcher:
            result = cmd_group_list(_make_args())
        assert "No groups" in result


class TestCmdGroupShow:
    def test_returns_member_keys(self):
        secrets = {"X": "1", f"{GROUP_PREFIX}g": "X"}
        patcher, mgr, vault = _patch(secrets)
        with patcher:
            result = cmd_group_show(_make_args(group="g"))
        assert "X" in result


class TestCmdGroupExport:
    def test_returns_key_value_lines(self):
        secrets = {"HOST": "localhost", f"{GROUP_PREFIX}db": "HOST"}
        patcher, mgr, vault = _patch(secrets)
        with patcher:
            result = cmd_group_export(_make_args(group="db"))
        assert "HOST=localhost" in result
