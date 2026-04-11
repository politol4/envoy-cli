"""Integration-style tests: copy_commands wired to a real Vault."""

import argparse
import os
import tempfile
import unittest
from unittest.mock import patch

from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault
from envoy_cli.copy_commands import cmd_copy, cmd_move


PASS = "integration-pass"
ENV = "test"


def _args(**kwargs):
    defaults = dict(
        env=ENV,
        passphrase=PASS,
        base_url="",
        token="",
        src_key="SRC",
        dst_key="DST",
        overwrite=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestCopyIntegration(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _manager(self):
        m = SyncManager.__new__(SyncManager)
        m.env = ENV
        m.passphrase = PASS
        m.base_url = ""
        m.token = ""
        m._dir = self.tmp
        return m

    def _seed_vault(self, secrets):
        """Write a real vault file with *secrets*."""
        m = self._manager()
        v = m._load_vault()
        for k, val in secrets.items():
            v.set(k, val)
        m._save_vault(v)

    def test_copy_persists_to_disk(self):
        self._seed_vault({"SRC": "hello"})
        with patch("envoy_cli.copy_commands._make_manager", side_effect=lambda a: self._manager()):
            cmd_copy(_args())
        m = self._manager()
        v = m._load_vault()
        self.assertEqual(v.get("DST"), "hello")

    def test_move_removes_src_on_disk(self):
        self._seed_vault({"SRC": "hello"})
        with patch("envoy_cli.copy_commands._make_manager", side_effect=lambda a: self._manager()):
            cmd_move(_args())
        m = self._manager()
        v = m._load_vault()
        self.assertIsNone(v.get("SRC"))
        self.assertEqual(v.get("DST"), "hello")


if __name__ == "__main__":
    unittest.main()
