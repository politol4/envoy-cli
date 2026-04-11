"""Tests for envoy_cli/copy_commands.py."""

import argparse
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.copy_commands import cmd_copy, cmd_move


def _make_args(**kwargs):
    defaults = dict(
        env="development",
        passphrase="pass",
        base_url="http://localhost",
        token="tok",
        src_key="OLD",
        dst_key="NEW",
        overwrite=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_manager(secrets=None):
    secrets = secrets or {"OLD": "value"}
    vault = MagicMock()
    vault.all.return_value = dict(secrets)
    vault._secrets = dict(secrets)

    def _set(k, v):
        vault._secrets[k] = v

    def _delete(k):
        vault._secrets.pop(k, None)

    vault.set.side_effect = _set
    vault.delete.side_effect = _delete

    manager = MagicMock()
    manager._load_vault.return_value = vault
    manager._save_vault = MagicMock()
    return manager, vault


class TestCmdCopy(unittest.TestCase):

    def _patch(self, secrets=None):
        manager, vault = _make_manager(secrets)
        patcher = patch("envoy_cli.copy_commands._make_manager", return_value=manager)
        return patcher, manager, vault

    def test_returns_string(self):
        patcher, manager, vault = self._patch()
        with patcher:
            result = cmd_copy(_make_args())
        self.assertIsInstance(result, str)

    def test_copy_success_message_contains_keys(self):
        patcher, manager, vault = self._patch()
        with patcher:
            result = cmd_copy(_make_args(src_key="OLD", dst_key="NEW"))
        self.assertIn("OLD", result)
        self.assertIn("NEW", result)

    def test_copy_success_message_contains_env(self):
        patcher, manager, vault = self._patch()
        with patcher:
            result = cmd_copy(_make_args(env="staging"))
        self.assertIn("staging", result)

    def test_copy_error_returns_error_message(self):
        patcher, manager, vault = self._patch(secrets={})
        with patcher:
            result = cmd_copy(_make_args(src_key="MISSING", dst_key="DST"))
        self.assertIn("Error", result)

    def test_vault_saved_after_copy(self):
        patcher, manager, vault = self._patch()
        with patcher:
            cmd_copy(_make_args())
        manager._save_vault.assert_called_once()

    def test_move_removes_src_message(self):
        patcher, manager, vault = self._patch()
        with patcher:
            result = cmd_move(_make_args(src_key="OLD", dst_key="NEW"))
        self.assertIn("moved", result)

    def test_move_error_returns_error_message(self):
        patcher, manager, vault = self._patch(secrets={})
        with patcher:
            result = cmd_move(_make_args(src_key="MISSING", dst_key="DST"))
        self.assertIn("Error", result)


if __name__ == "__main__":
    unittest.main()
