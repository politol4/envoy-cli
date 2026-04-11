"""Tests for envoy_cli.watch and envoy_cli.watch_commands."""

import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.watch import FileWatcher, WatchError
from envoy_cli.watch_commands import cmd_watch


class TestFileWatcher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".env")
        self.tmp.write(b"KEY=value\n")
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_empty_path_raises(self):
        with self.assertRaises(WatchError):
            FileWatcher(path="", callback=lambda p: None)

    def test_non_positive_interval_raises(self):
        with self.assertRaises(WatchError):
            FileWatcher(path=self.tmp.name, callback=lambda p: None, interval=0)

    def test_check_once_fires_callback_on_mtime_change(self):
        fired = []
        watcher = FileWatcher(
            path=self.tmp.name,
            callback=lambda p: fired.append(p),
            interval=0.05,
        )
        # Prime the baseline.
        watcher._last_mtime = os.path.getmtime(self.tmp.name) - 1
        watcher.check_once()
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0], self.tmp.name)

    def test_check_once_no_fire_when_mtime_unchanged(self):
        fired = []
        watcher = FileWatcher(
            path=self.tmp.name,
            callback=lambda p: fired.append(p),
        )
        watcher._last_mtime = os.path.getmtime(self.tmp.name)
        watcher.check_once()
        self.assertEqual(len(fired), 0)

    def test_check_once_returns_false_for_missing_file(self):
        watcher = FileWatcher(
            path="/nonexistent/__no_such_file__.env",
            callback=lambda p: None,
        )
        result = watcher.check_once()
        self.assertFalse(result)

    def test_start_fires_callback_after_modification(self):
        fired = []
        watcher = FileWatcher(
            path=self.tmp.name,
            callback=lambda p: fired.append(p),
            interval=0.05,
        )
        # Modify the file after a short delay in a thread.
        import threading

        def _modify():
            time.sleep(0.08)
            with open(self.tmp.name, "ab") as f:
                f.write(b"EXTRA=1\n")

        t = threading.Thread(target=_modify, daemon=True)
        t.start()
        watcher.start(max_iterations=5)
        t.join(timeout=1)
        self.assertGreaterEqual(len(fired), 1)

    def test_stop_exits_loop(self):
        watcher = FileWatcher(
            path=self.tmp.name,
            callback=lambda p: None,
            interval=0.05,
        )
        import threading

        t = threading.Thread(target=watcher.start, daemon=True)
        t.start()
        time.sleep(0.12)
        watcher.stop()
        t.join(timeout=1)
        self.assertFalse(t.is_alive())


class TestCmdWatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".env")
        self.tmp.write(b"FOO=bar\n")
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _make_args(self, **kwargs):
        defaults = dict(file=self.tmp.name, env="dev", interval=0.05, fmt="dotenv")
        defaults.update(kwargs)
        ns = MagicMock()
        for k, v in defaults.items():
            setattr(ns, k, v)
        return ns

    def test_missing_file_raises_watch_error(self):
        args = self._make_args(file="/no/such/file.env")
        manager = MagicMock()
        with self.assertRaises(WatchError):
            cmd_watch(args, manager, max_iterations=0)

    def test_returns_stopped_message(self):
        args = self._make_args()
        manager = MagicMock()
        with patch("envoy_cli.watch_commands.import_from_file"):
            result = cmd_watch(args, manager, max_iterations=0)
        self.assertIn("Stopped watching", result)
        self.assertIn("dev", result)

    def test_import_called_on_file_change(self):
        args = self._make_args(interval=0.05)
        manager = MagicMock()
        import threading

        call_log = []

        def fake_import(**kwargs):
            call_log.append(kwargs)

        def _run():
            with patch("envoy_cli.watch_commands.import_from_file", side_effect=fake_import):
                cmd_watch(args, manager, max_iterations=3)

        # Modify the file mid-run.
        def _modify():
            time.sleep(0.08)
            with open(self.tmp.name, "ab") as f:
                f.write(b"BAR=baz\n")

        t_mod = threading.Thread(target=_modify, daemon=True)
        t_run = threading.Thread(target=_run, daemon=True)
        t_run.start()
        t_mod.start()
        t_run.join(timeout=2)
        self.assertGreaterEqual(len(call_log), 1)
        self.assertEqual(call_log[0]["env"], "dev")


if __name__ == "__main__":
    unittest.main()
