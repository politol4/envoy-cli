"""Tests for envoy_cli.pin_commands module."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from envoy_cli.pin import PinError, pin_key
from envoy_cli.pin_commands import (
    cmd_pin_list,
    cmd_pin_remove,
    cmd_pin_set,
    cmd_pin_status,
)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"profile": "default", "env": "development", "passphrase": "pass"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_vault(secrets: dict):
    vault = MagicMock()
    vault.secrets = secrets
    vault.save = MagicMock()
    return vault


def _patch_manager(vault):
    manager = MagicMock()
    manager._load_vault.return_value = vault
    return manager


class TestCmdPinSet:
    def test_returns_confirmation(self):
        vault = _make_vault({"API_KEY": "secret"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_set(_make_args(key="API_KEY"))
        assert "pinned" in result
        assert "API_KEY" in result

    def test_vault_saved_after_pin(self):
        vault = _make_vault({"API_KEY": "secret"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            cmd_pin_set(_make_args(key="API_KEY"))
        vault.save.assert_called_once_with("pass")

    def test_missing_key_raises(self):
        vault = _make_vault({"API_KEY": "secret"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            with pytest.raises(PinError):
                cmd_pin_set(_make_args(key="MISSING"))


class TestCmdPinRemove:
    def test_returns_unpinned_message(self):
        secrets = pin_key({"API_KEY": "secret"}, "API_KEY")
        vault = _make_vault(secrets)
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_remove(_make_args(key="API_KEY"))
        assert "unpinned" in result

    def test_not_pinned_raises(self):
        vault = _make_vault({"API_KEY": "secret"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            with pytest.raises(PinError):
                cmd_pin_remove(_make_args(key="API_KEY"))


class TestCmdPinList:
    def test_lists_pinned_keys(self):
        secrets = pin_key({"A": "1", "B": "2"}, "A")
        vault = _make_vault(secrets)
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_list(_make_args())
        assert "A" in result
        assert "B" not in result

    def test_no_pinned_keys_message(self):
        vault = _make_vault({"A": "1"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_list(_make_args())
        assert "No pinned" in result


class TestCmdPinStatus:
    def test_pinned_status(self):
        secrets = pin_key({"TOKEN": "xyz"}, "TOKEN")
        vault = _make_vault(secrets)
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_status(_make_args(key="TOKEN"))
        assert "pinned" in result

    def test_not_pinned_status(self):
        vault = _make_vault({"TOKEN": "xyz"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            result = cmd_pin_status(_make_args(key="TOKEN"))
        assert "not pinned" in result

    def test_missing_key_raises(self):
        vault = _make_vault({"TOKEN": "xyz"})
        with patch("envoy_cli.pin_commands._make_manager", return_value=_patch_manager(vault)):
            with pytest.raises(PinError):
                cmd_pin_status(_make_args(key="MISSING"))
