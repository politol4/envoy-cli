"""Tests for envoy_cli.ttl_commands."""

from __future__ import annotations

import argparse
import time
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.ttl import _meta_key, set_ttl
from envoy_cli.ttl_commands import (
    cmd_ttl_get,
    cmd_ttl_list_expiring,
    cmd_ttl_purge,
    cmd_ttl_remove,
    cmd_ttl_set,
)


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"env": "dev", "key": "DB_URL", "seconds": 60, "within": 3600}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_manager(secrets: dict):
    vault = MagicMock()
    vault.secrets = secrets
    manager = MagicMock()
    manager.load_vault.return_value = vault
    return manager, vault


class TestCmdTTLSet(unittest.TestCase):
    def _run(self, secrets, **kwargs):
        manager, vault = _make_manager(secrets)
        args = _make_args(**kwargs)
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_set(args)
        return result, manager, vault

    def test_returns_confirmation_message(self):
        result, _, _ = self._run({"DB_URL": "postgres://"}, seconds=120)
        self.assertIn("120s", result)
        self.assertIn("DB_URL", result)

    def test_vault_saved_after_set(self):
        _, manager, _ = self._run({"DB_URL": "postgres://"})
        manager.save_vault.assert_called_once()

    def test_missing_key_raises_system_exit(self):
        manager, _ = _make_manager({})
        args = _make_args(key="MISSING")
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            with self.assertRaises(SystemExit):
                cmd_ttl_set(args)


class TestCmdTTLGet(unittest.TestCase):
    def test_no_ttl_message(self):
        manager, _ = _make_manager({"DB_URL": "x"})
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_get(args)
        self.assertIn("No TTL", result)

    def test_remaining_seconds_shown(self):
        secrets = set_ttl({"DB_URL": "x"}, "DB_URL", 300)
        manager, _ = _make_manager(secrets)
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_get(args)
        self.assertIn("expires in", result)


class TestCmdTTLRemove(unittest.TestCase):
    def test_removes_meta_key(self):
        secrets = set_ttl({"DB_URL": "x"}, "DB_URL", 60)
        manager, vault = _make_manager(secrets)
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            cmd_ttl_remove(args)
        self.assertNotIn(_meta_key("DB_URL"), vault.secrets)

    def test_returns_confirmation(self):
        manager, _ = _make_manager({"DB_URL": "x"})
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_remove(args)
        self.assertIn("removed", result)


class TestCmdTTLPurge(unittest.TestCase):
    def test_no_expired_message(self):
        manager, _ = _make_manager({"DB_URL": "x"})
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_purge(args)
        self.assertIn("No expired", result)

    def test_expired_key_reported(self):
        secrets = {"DB_URL": "x", _meta_key("DB_URL"): str(int(time.time()) - 5)}
        manager, _ = _make_manager(secrets)
        args = _make_args()
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_purge(args)
        self.assertIn("DB_URL", result)


class TestCmdTTLListExpiring(unittest.TestCase):
    def test_none_expiring_message(self):
        manager, _ = _make_manager({"DB_URL": "x"})
        args = _make_args(within=60)
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_list_expiring(args)
        self.assertIn("No secrets", result)

    def test_expiring_key_listed(self):
        secrets = set_ttl({"DB_URL": "x"}, "DB_URL", 30)
        manager, _ = _make_manager(secrets)
        args = _make_args(within=3600)
        with patch("envoy_cli.ttl_commands._make_manager", return_value=manager):
            result = cmd_ttl_list_expiring(args)
        self.assertIn("DB_URL", result)
        self.assertIn("remaining", result)
