"""Tests for envoy_cli.label_commands."""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from envoy_cli.label import META_SUFFIX, _meta_key, add_label
from envoy_cli.label_commands import (
    cmd_label_add,
    cmd_label_find,
    cmd_label_list,
    cmd_label_remove,
)


def _make_args(**kwargs) -> Namespace:
    defaults = {"env": "test"}
    defaults.update(kwargs)
    return Namespace(**defaults)


def _make_vault(secrets: dict):
    vault = MagicMock()
    vault.secrets = secrets
    return vault


def _patch_manager(vault):
    manager = MagicMock()
    manager._load_vault.return_value = vault
    manager._save_vault = MagicMock()
    return manager


class TestCmdLabelAdd:
    def _run(self, secrets, key, label):
        vault = _make_vault(dict(secrets))
        manager = _patch_manager(vault)
        args = _make_args(key=key, label=label)
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            return cmd_label_add(args), manager, vault

    def test_returns_confirmation(self):
        msg, _, _ = self._run({"X": "1"}, "X", "core")
        assert "core" in msg
        assert "X" in msg

    def test_vault_saved_after_add(self):
        _, manager, vault = self._run({"X": "1"}, "X", "core")
        manager._save_vault.assert_called_once_with(vault)

    def test_label_present_in_updated_secrets(self):
        vault = _make_vault({"X": "1"})
        manager = _patch_manager(vault)
        args = _make_args(key="X", label="core")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            cmd_label_add(args)
        labels = json.loads(vault.secrets[_meta_key("X")])
        assert "core" in labels

    def test_missing_key_raises_system_exit(self):
        vault = _make_vault({})
        manager = _patch_manager(vault)
        args = _make_args(key="MISSING", label="x")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            with pytest.raises(SystemExit):
                cmd_label_add(args)


class TestCmdLabelRemove:
    def _seed(self):
        s = {"DB": "url"}
        return add_label(s, "DB", "infra")

    def test_returns_confirmation(self):
        vault = _make_vault(self._seed())
        manager = _patch_manager(vault)
        args = _make_args(key="DB", label="infra")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            msg = cmd_label_remove(args)
        assert "infra" in msg

    def test_missing_label_raises_system_exit(self):
        vault = _make_vault({"DB": "url"})
        manager = _patch_manager(vault)
        args = _make_args(key="DB", label="ghost")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            with pytest.raises(SystemExit):
                cmd_label_remove(args)


class TestCmdLabelList:
    def test_returns_labels_one_per_line(self):
        s = add_label({"K": "v"}, "K", "alpha")
        s = add_label(s, "K", "beta")
        vault = _make_vault(s)
        manager = _patch_manager(vault)
        args = _make_args(key="K")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            msg = cmd_label_list(args)
        assert "alpha" in msg
        assert "beta" in msg

    def test_no_labels_returns_informative_message(self):
        vault = _make_vault({"K": "v"})
        manager = _patch_manager(vault)
        args = _make_args(key="K")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            msg = cmd_label_list(args)
        assert "No labels" in msg


class TestCmdLabelFind:
    def test_returns_matching_keys(self):
        s = add_label({"A": "1", "B": "2"}, "A", "shared")
        vault = _make_vault(s)
        manager = _patch_manager(vault)
        args = _make_args(label="shared")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            msg = cmd_label_find(args)
        assert "A" in msg

    def test_no_matches_returns_informative_message(self):
        vault = _make_vault({"A": "1"})
        manager = _patch_manager(vault)
        args = _make_args(label="ghost")
        with patch("envoy_cli.label_commands._make_manager", return_value=manager):
            msg = cmd_label_find(args)
        assert "No keys" in msg
