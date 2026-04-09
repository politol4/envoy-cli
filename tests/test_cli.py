"""Tests for the envoy_cli.cli module."""

import json
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO

from envoy_cli.cli import build_parser, run


BASE_ARGS = ["--passphrase", "secret", "--vault", "/tmp/test.vault"]


class TestCLIParser(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_set_command_parsed(self):
        args = self.parser.parse_args(BASE_ARGS + ["set", "FOO", "bar"])
        self.assertEqual(args.command, "set")
        self.assertEqual(args.key, "FOO")
        self.assertEqual(args.value, "bar")

    def test_get_command_parsed(self):
        args = self.parser.parse_args(BASE_ARGS + ["get", "FOO"])
        self.assertEqual(args.command, "get")
        self.assertEqual(args.key, "FOO")

    def test_delete_command_parsed(self):
        args = self.parser.parse_args(BASE_ARGS + ["delete", "FOO"])
        self.assertEqual(args.command, "delete")

    def test_list_command_parsed(self):
        args = self.parser.parse_args(BASE_ARGS + ["list"])
        self.assertEqual(args.command, "list")

    def test_push_requires_url_and_token(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(BASE_ARGS + ["push"])

    def test_export_default_output(self):
        args = self.parser.parse_args(BASE_ARGS + ["export"])
        self.assertEqual(args.output, ".env")

    def test_import_default_input(self):
        args = self.parser.parse_args(BASE_ARGS + ["import"])
        self.assertEqual(args.input, ".env")


class TestCLIRun(unittest.TestCase):
    def _run(self, extra_args, vault_mock):
        with patch("envoy_cli.cli.Vault", return_value=vault_mock):
            run(BASE_ARGS + extra_args)

    def _make_vault(self):
        v = MagicMock()
        v.get.return_value = "myvalue"
        v.keys.return_value = ["FOO", "BAR"]
        v.all.return_value = {"FOO": "1", "BAR": "2"}
        return v

    def test_set_calls_vault_set(self):
        vault = self._make_vault()
        self._run(["set", "FOO", "bar"], vault)
        vault.set.assert_called_once_with("FOO", "bar")

    def test_get_prints_value(self):
        vault = self._make_vault()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            self._run(["get", "FOO"], vault)
            self.assertIn("myvalue", mock_out.getvalue())

    def test_get_missing_key_exits(self):
        vault = self._make_vault()
        vault.get.return_value = None
        with self.assertRaises(SystemExit) as ctx:
            self._run(["get", "MISSING"], vault)
        self.assertEqual(ctx.exception.code, 1)

    def test_delete_calls_vault_delete(self):
        vault = self._make_vault()
        self._run(["delete", "FOO"], vault)
        vault.delete.assert_called_once_with("FOO")

    def test_list_prints_keys(self):
        vault = self._make_vault()
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            self._run(["list"], vault)
            output = mock_out.getvalue()
            self.assertIn("BAR", output)
            self.assertIn("FOO", output)

    def test_export_calls_save_file(self):
        vault = self._make_vault()
        with patch("envoy_cli.cli.save_file") as mock_save:
            self._run(["export", "/tmp/out.env"], vault)
            mock_save.assert_called_once_with("/tmp/out.env", {"FOO": "1", "BAR": "2"})

    def test_import_calls_vault_set_for_each_key(self):
        vault = self._make_vault()
        with patch("envoy_cli.cli.load_file", return_value={"A": "1", "B": "2"}):
            self._run(["import", "/tmp/in.env"], vault)
        self.assertEqual(vault.set.call_count, 2)

    def test_push_calls_sync_manager_push(self):
        vault = self._make_vault()
        mock_client = MagicMock()
        mock_manager = MagicMock()
        with patch("envoy_cli.cli.RemoteClient", return_value=mock_client), \
             patch("envoy_cli.cli.SyncManager", return_value=mock_manager), \
             patch("envoy_cli.cli.Vault", return_value=vault):
            run(BASE_ARGS + ["push", "--url", "http://x", "--token", "tok", "--env", "staging"])
        mock_manager.push.assert_called_once_with("staging")


if __name__ == "__main__":
    unittest.main()
