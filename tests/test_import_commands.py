"""Tests for envoy_cli.import_commands."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from envoy_cli.import_commands import cmd_import_file, cmd_import_stdin


def _make_args(**kwargs):
    defaults = {
        "profile": "default",
        "file": None,
        "fmt": None,
        "prefix": None,
        "no_overwrite": False,
    }
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    return ns


def _make_manager(existing=None):
    manager = MagicMock()
    manager.get_all.return_value = dict(existing or {})
    return manager


class TestCmdImportFile(unittest.TestCase):
    def _write_tmp(self, content: str, suffix: str = ".env") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_import_dotenv_file_reports_added(self):
        path = self._write_tmp("NEW_KEY=hello\n")
        manager = _make_manager()
        result = cmd_import_file(_make_args(file=path), manager=manager)
        self.assertIn("1 added", result)
        manager.set.assert_called_once_with("NEW_KEY", "hello")
        os.unlink(path)

    def test_import_json_file_reports_added(self):
        path = self._write_tmp(json.dumps({"A": "1", "B": "2"}), suffix=".json")
        manager = _make_manager()
        result = cmd_import_file(_make_args(file=path), manager=manager)
        self.assertIn("2 added", result)
        os.unlink(path)

    def test_import_updates_existing_key(self):
        path = self._write_tmp("FOO=new\n")
        manager = _make_manager(existing={"FOO": "old"})
        result = cmd_import_file(_make_args(file=path), manager=manager)
        self.assertIn("1 updated", result)
        os.unlink(path)

    def test_no_overwrite_preserves_existing(self):
        path = self._write_tmp("FOO=new\n")
        manager = _make_manager(existing={"FOO": "old"})
        result = cmd_import_file(_make_args(file=path, no_overwrite=True), manager=manager)
        self.assertEqual(result, "Nothing changed.")
        os.unlink(path)

    def test_missing_file_raises_system_exit(self):
        manager = _make_manager()
        with self.assertRaises(SystemExit):
            cmd_import_file(_make_args(file="/no/such/file.env"), manager=manager)

    def test_prefix_filter_applied(self):
        path = self._write_tmp("APP_X=1\nOTHER=2\n")
        manager = _make_manager()
        result = cmd_import_file(_make_args(file=path, prefix="APP_"), manager=manager)
        self.assertIn("1 added", result)
        manager.set.assert_called_once_with("APP_X", "1")
        os.unlink(path)


class TestCmdImportStdin(unittest.TestCase):
    def test_basic_stdin_import(self):
        manager = _make_manager()
        result = cmd_import_stdin(
            _make_args(), manager=manager, stdin_text="K=v\n"
        )
        self.assertIn("1 added", result)
        manager.set.assert_called_once_with("K", "v")

    def test_empty_stdin_raises_system_exit(self):
        manager = _make_manager()
        with self.assertRaises(SystemExit):
            cmd_import_stdin(_make_args(), manager=manager, stdin_text="")

    def test_json_format_stdin(self):
        manager = _make_manager()
        result = cmd_import_stdin(
            _make_args(fmt="json"),
            manager=manager,
            stdin_text=json.dumps({"X": "1"}),
        )
        self.assertIn("1 added", result)

    def test_nothing_changed_when_identical(self):
        manager = _make_manager(existing={"FOO": "bar"})
        result = cmd_import_stdin(
            _make_args(), manager=manager, stdin_text="FOO=bar\n"
        )
        self.assertEqual(result, "Nothing changed.")


if __name__ == "__main__":
    unittest.main()
