"""Tests for envoy_cli.notify and envoy_cli.notify_commands."""
from __future__ import annotations

import json
import os
import tempfile
import types
import unittest
from pathlib import Path

from envoy_cli.notify import (
    NotifyConfig,
    NotifyError,
    dispatch_notification,
)
from envoy_cli.notify_commands import (
    cmd_notify_add,
    cmd_notify_list,
    cmd_notify_remove,
)


# ---------------------------------------------------------------------------
# NotifyConfig
# ---------------------------------------------------------------------------

class TestNotifyConfig(unittest.TestCase):
    def test_to_dict_contains_required_fields(self):
        cfg = NotifyConfig(channel="slack", target="https://hooks.example.com")
        d = cfg.to_dict()
        self.assertEqual(d["channel"], "slack")
        self.assertEqual(d["target"], "https://hooks.example.com")
        self.assertIn("events", d)
        self.assertIn("enabled", d)

    def test_from_dict_round_trip(self):
        cfg = NotifyConfig(channel="log", target="/tmp/x.log", events=["set", "delete"])
        restored = NotifyConfig.from_dict(cfg.to_dict())
        self.assertEqual(restored.channel, cfg.channel)
        self.assertEqual(restored.target, cfg.target)
        self.assertEqual(restored.events, cfg.events)

    def test_from_dict_missing_channel_raises(self):
        with self.assertRaises(NotifyError):
            NotifyConfig.from_dict({"target": "x"})

    def test_from_dict_missing_target_raises(self):
        with self.assertRaises(NotifyError):
            NotifyConfig.from_dict({"channel": "log"})

    def test_default_events_is_empty(self):
        cfg = NotifyConfig.from_dict({"channel": "log", "target": "f.log"})
        self.assertEqual(cfg.events, [])


# ---------------------------------------------------------------------------
# dispatch_notification
# ---------------------------------------------------------------------------

class TestDispatchNotification(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".log")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_log_channel_writes_json_line(self):
        cfg = NotifyConfig(channel="log", target=self.tmp)
        dispatch_notification([cfg], event="set", env="staging")
        with open(self.tmp) as fh:
            data = json.loads(fh.readline())
        self.assertEqual(data["event"], "set")
        self.assertEqual(data["env"], "staging")

    def test_returns_count_of_dispatched(self):
        cfg = NotifyConfig(channel="log", target=self.tmp)
        n = dispatch_notification([cfg, cfg], event="set", env="prod")
        self.assertEqual(n, 2)

    def test_event_filter_skips_non_matching(self):
        cfg = NotifyConfig(channel="log", target=self.tmp, events=["delete"])
        n = dispatch_notification([cfg], event="set", env="dev")
        self.assertEqual(n, 0)
        self.assertFalse(os.path.exists(self.tmp))

    def test_disabled_config_skipped(self):
        cfg = NotifyConfig(channel="log", target=self.tmp, enabled=False)
        n = dispatch_notification([cfg], event="set", env="dev")
        self.assertEqual(n, 0)

    def test_empty_event_raises(self):
        with self.assertRaises(NotifyError):
            dispatch_notification([], event="", env="dev")

    def test_slack_channel_calls_http_post(self):
        calls = []
        cfg = NotifyConfig(channel="slack", target="https://hooks.example.com")
        dispatch_notification([cfg], event="set", env="prod", _http_post=lambda u, p: calls.append((u, p)))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "https://hooks.example.com")

    def test_unknown_channel_raises(self):
        cfg = NotifyConfig(channel="carrier_pigeon", target="somewhere")
        with self.assertRaises(NotifyError):
            dispatch_notification([cfg], event="set", env="devn# ---------------------------------------------------------------------------
# notify_commands
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    base = {"env", "channel": "log", "target": "/tmp/t.log",
            "events": [], "base_dir": None}
    base.update(kwargs)
    ns = types.SimpleNamespace(**base)
    return ns


class TestCmdNotify(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdten
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _args(self, **kw):
        a = _make_args(**kw)
        a.base_dir = self.tmpdir
        return a

    def test_add_returns_confirmation(self):
        msg = cmd_notify_add(self._args())
        self.assertIn("staging", msg)
        self.assertIn("log", msg)

    def test_list_shows_added_config(self):
        cmd_notify_add(self._args())
        msg = cmd_notify_list(self._args())
        self.assertIn("log", msg)
        self.assertIn("/tmp/t.log", msg)

    def test_list_empty_message_when_none(self):
        msg = cmd_notify_list(self._args())
        self.assertIn("No notification", msg)

    def test_remove_config(self):
        cmd_notify_add(self._args())
        msg = cmd_notify_remove(self._args())
        self.assertIn("removed", msg)
        after = cmd_notify_list(self._args())
        self.assertIn("No notification", after)

    def test_remove_nonexistent_raises(self):
        with self.assertRaises(NotifyError):
            cmd_notify_remove(self._args())


if __name__ == "__main__":
    unittest.main()
