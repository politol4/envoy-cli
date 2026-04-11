"""Tests for envoy_cli/access_commands.py"""
import types
import pytest
from unittest.mock import MagicMock, patch

from envoy_cli.access_commands import (
    cmd_access_set,
    cmd_access_remove,
    cmd_access_show,
    cmd_access_check,
    cmd_access_list_user,
)


def _make_args(**kwargs):
    defaults = {"passphrase": "pass", "env": "local", "key": "DB_URL",
                "user": "alice", "role": "read"}
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _make_vault(secrets=None):
    vault = MagicMock()
    vault.secrets = secrets or {"DB_URL": "postgres://localhost", "API_KEY": "secret"}
    return vault


def _patch_manager(vault):
    manager = MagicMock()
    manager._load_vault.return_value = vault
    manager._save_vault = MagicMock()
    return manager


class TestCmdAccessSet:
    def test_returns_confirmation(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_set(_make_args(key="DB_URL", user="alice", role="read"))
        assert "alice" in result
        assert "read" in result
        assert "DB_URL" in result

    def test_vault_saved_after_set(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            cmd_access_set(_make_args(key="DB_URL", user="alice", role="write"))
        manager._save_vault.assert_called_once()

    def test_invalid_role_raises_system_exit(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            with pytest.raises(SystemExit):
                cmd_access_set(_make_args(role="superuser"))


class TestCmdAccessRemove:
    def test_returns_confirmation(self):
        from envoy_cli.access import set_access
        secrets = set_access({"DB_URL": "x"}, "DB_URL", "read", "alice")
        vault = _make_vault(secrets=secrets)
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_remove(_make_args(key="DB_URL", user="alice"))
        assert "alice" in result
        assert "DB_URL" in result

    def test_missing_user_raises_system_exit(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            with pytest.raises(SystemExit):
                cmd_access_remove(_make_args(user="ghost"))


class TestCmdAccessShow:
    def test_no_entries_message(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_show(_make_args(key="DB_URL"))
        assert "No access entries" in result

    def test_shows_user_and_role(self):
        from envoy_cli.access import set_access
        secrets = set_access({"DB_URL": "x"}, "DB_URL", "admin", "bob")
        vault = _make_vault(secrets=secrets)
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_show(_make_args(key="DB_URL"))
        assert "bob" in result
        assert "admin" in result


class TestCmdAccessCheck:
    def test_allowed_message(self):
        from envoy_cli.access import set_access
        secrets = set_access({"DB_URL": "x"}, "DB_URL", "write", "alice")
        vault = _make_vault(secrets=secrets)
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_check(_make_args(key="DB_URL", user="alice", role="read"))
        assert "ALLOWED" in result

    def test_denied_message(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_check(_make_args(key="DB_URL", user="nobody", role="read"))
        assert "DENIED" in result


class TestCmdAccessListUser:
    def test_no_keys_message(self):
        vault = _make_vault()
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_list_user(_make_args(user="nobody"))
        assert "No access entries" in result

    def test_lists_accessible_keys(self):
        from envoy_cli.access import set_access
        secrets = set_access({"DB_URL": "x", "API_KEY": "y"}, "DB_URL", "read", "alice")
        vault = _make_vault(secrets=secrets)
        manager = _patch_manager(vault)
        with patch("envoy_cli.access_commands._make_manager", return_value=manager):
            result = cmd_access_list_user(_make_args(user="alice"))
        assert "DB_URL" in result
