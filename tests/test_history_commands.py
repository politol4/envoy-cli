"""Tests for envoy_cli.history_commands."""
import os
import tempfile
import unittest
from argparse import Namespace

from envoy_cli.history import History, HistoryEntry
from envoy_cli.history_commands import (
    cmd_history_clear,
    cmd_history_list,
    cmd_history_show_key,
    _history_path,
)


def _make_args(**kwargs) -> Namespace:
    defaults = dict(vault_dir=tempfile.mkdtemp(), env="dev", key=None)
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestCmdHistoryList(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _args(self, **kw):
        return _make_args(vault_dir=self._tmp, **kw)

    def _seed(self, args, entries):
        h = History(_history_path(args))
        for e in entries:
            h.record(e)

    def test_empty_history_returns_message(self):
        args = self._args()
        result = cmd_history_list(args)
        self.assertIn("No history", result)

    def test_list_shows_action_and_key(self):
        args = self._args()
        self._seed(args, [HistoryEntry(action="set", key="DB_URL", env="dev")])
        result = cmd_history_list(args)
        self.assertIn("SET", result)
        self.assertIn("DB_URL", result)

    def test_list_filters_by_key(self):
        args = self._args(key="ONLY")
        self._seed(args, [
            HistoryEntry(action="set", key="ONLY", env="dev"),
            HistoryEntry(action="set", key="OTHER", env="dev"),
        ])
        result = cmd_history_list(args)
        self.assertIn("ONLY", result)
        self.assertNotIn("OTHER", result)

    def test_note_appears_in_output(self):
        args = self._args()
        self._seed(args, [HistoryEntry(action="set", key="X", env="dev", note="initial")])
        result = cmd_history_list(args)
        self.assertIn("initial", result)


class TestCmdHistoryClear(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _args(self, **kw):
        return _make_args(vault_dir=self._tmp, **kw)

    def test_clear_reports_count(self):
        args = self._args()
        h = History(_history_path(args))
        h.record(HistoryEntry(action="set", key="A", env="dev"))
        h.record(HistoryEntry(action="set", key="B", env="dev"))
        result = cmd_history_clear(args)
        self.assertIn("2", result)

    def test_clear_empty_history(self):
        args = self._args()
        result = cmd_history_clear(args)
        self.assertIn("0", result)


class TestCmdHistoryShowKey(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _args(self, **kw):
        return _make_args(vault_dir=self._tmp, **kw)

    def test_no_history_for_key(self):
        args = self._args(key="MISSING")
        result = cmd_history_show_key(args)
        self.assertIn("No history", result)

    def test_shows_all_actions_for_key(self):
        args = self._args(key="DB")
        h = History(_history_path(args))
        h.record(HistoryEntry(action="set", key="DB", env="dev"))
        h.record(HistoryEntry(action="delete", key="DB", env="dev"))
        result = cmd_history_show_key(args)
        self.assertIn("SET", result)
        self.assertIn("DELETE", result)
