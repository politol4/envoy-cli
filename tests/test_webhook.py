"""Tests for envoy_cli.webhook and envoy_cli.webhook_commands."""
from __future__ import annotations

import json
import os
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

from envoy_cli.webhook import (
    WebhookConfig,
    WebhookError,
    _build_payload,
    dispatch,
    dispatch_all,
)
from envoy_cli.webhook_commands import (
    cmd_webhook_add,
    cmd_webhook_list,
    cmd_webhook_remove,
    cmd_webhook_test,
)


# ---------------------------------------------------------------------------
# WebhookConfig
# ---------------------------------------------------------------------------

class TestWebhookConfig(unittest.TestCase):
    def test_to_dict_contains_required_fields(self):
        cfg = WebhookConfig(url="https://example.com/hook", events=["set"])
        d = cfg.to_dict()
        self.assertEqual(d["url"], "https://example.com/hook")
        self.assertEqual(d["events"], ["set"])

    def test_from_dict_round_trip(self):
        cfg = WebhookConfig(url="https://example.com", events=["delete"], timeout=10)
        restored = WebhookConfig.from_dict(cfg.to_dict())
        self.assertEqual(restored.url, cfg.url)
        self.assertEqual(restored.timeout, 10)

    def test_from_dict_missing_url_raises(self):
        with self.assertRaises(WebhookError):
            WebhookConfig.from_dict({"events": []})

    def test_empty_events_means_all(self):
        cfg = WebhookConfig(url="https://x.io")
        self.assertEqual(cfg.events, [])


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

class TestDispatch(unittest.TestCase):
    def _cfg(self, events=None):
        return WebhookConfig(url="https://hook.example.com/", events=events or [])

    @patch("envoy_cli.webhook.urllib.request.urlopen")
    def test_dispatch_posts_json(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        dispatch(self._cfg(), event="set", env="production", key="DB_URL")
        self.assertTrue(mock_open.called)
        req = mock_open.call_args[0][0]
        self.assertIn(b"DB_URL", req.data)

    @patch("envoy_cli.webhook.urllib.request.urlopen")
    def test_event_filter_skips_non_matching(self, mock_open):
        dispatch(self._cfg(events=["delete"]), event="set", env="staging", key="X")
        mock_open.assert_not_called()

    @patch("envoy_cli.webhook.urllib.request.urlopen")
    def test_url_error_raises_webhook_error(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.URLError("connection refused")
        with self.assertRaises(WebhookError):
            dispatch(self._cfg(), event="set", env="local", key="K")

    @patch("envoy_cli.webhook.urllib.request.urlopen")
    def test_dispatch_all_collects_errors(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.URLError("timeout")
        cfgs = [self._cfg(), self._cfg()]
        errors = dispatch_all(cfgs, event="set", env="local")
        self.assertEqual(len(errors), 2)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def _args(**kwargs):
    ns = types.SimpleNamespace(base_dir=tempfile.mkdtemp(), **kwargs)
    return ns


class TestWebhookCommands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _args(self, **kwargs):
        return types.SimpleNamespace(base_dir=self.tmp, **kwargs)

    def test_add_returns_message(self):
        msg = cmd_webhook_add(self._args(url="https://a.io", events="", secret_header=None, timeout=5))
        self.assertIn("https://a.io", msg)

    def test_list_shows_added_webhook(self):
        cmd_webhook_add(self._args(url="https://b.io", events="set,delete", secret_header=None, timeout=5))
        out = cmd_webhook_list(self._args())
        self.assertIn("https://b.io", out)

    def test_remove_deletes_webhook(self):
        cmd_webhook_add(self._args(url="https://c.io", events="", secret_header=None, timeout=5))
        cmd_webhook_remove(self._args(url="https://c.io"))
        out = cmd_webhook_list(self._args())
        self.assertNotIn("https://c.io", out)

    def test_remove_nonexistent_raises(self):
        with self.assertRaises(WebhookError):
            cmd_webhook_remove(self._args(url="https://nope.io"))

    def test_list_empty_returns_message(self):
        out = cmd_webhook_list(self._args())
        self.assertIn("No webhooks", out)

    @patch("envoy_cli.webhook_commands.dispatch")
    def test_webhook_test_calls_dispatch(self, mock_dispatch):
        cmd_webhook_add(self._args(url="https://d.io", events="", secret_header=None, timeout=5))
        msg = cmd_webhook_test(self._args(url="https://d.io"))
        self.assertTrue(mock_dispatch.called)
        self.assertIn("https://d.io", msg)

    def test_webhook_test_unknown_url_raises(self):
        with self.assertRaises(WebhookError):
            cmd_webhook_test(self._args(url="https://unknown.io"))


if __name__ == "__main__":
    unittest.main()
