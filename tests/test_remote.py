"""Unit tests for envoy_cli.remote.RemoteClient."""

import json
import unittest
from io import BytesIO
from unittest.mock import patch, MagicMock

from envoy_cli.remote import RemoteClient, RemoteError


def _mock_response(body: dict, status: int = 200):
    """Return a mock that behaves like an urllib response context manager."""
    raw = json.dumps(body).encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = raw
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestRemoteClient(unittest.TestCase):

    def setUp(self):
        self.client = RemoteClient("https://example.com", token="tok-abc")

    # ------------------------------------------------------------------
    # Constructor validation
    # ------------------------------------------------------------------

    def test_invalid_base_url_raises(self):
        with self.assertRaises(ValueError):
            RemoteClient("ftp://bad.url", token="x")

    def test_trailing_slash_stripped(self):
        c = RemoteClient("https://example.com/", token="x")
        self.assertEqual(c.base_url, "https://example.com")

    # ------------------------------------------------------------------
    # push
    # ------------------------------------------------------------------

    @patch("envoy_cli.remote.urllib.request.urlopen")
    def test_push_sends_correct_payload(self, mock_open):
        mock_open.return_value = _mock_response({"ok": True})
        result = self.client.push("production", "ENCRYPTED_DATA")
        self.assertEqual(result, {"ok": True})
        call_args = mock_open.call_args
        req = call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["profile"], "production")
        self.assertEqual(body["data"], "ENCRYPTED_DATA")
        self.assertEqual(req.get_method(), "PUT")

    # ------------------------------------------------------------------
    # pull
    # ------------------------------------------------------------------

    @patch("envoy_cli.remote.urllib.request.urlopen")
    def test_pull_returns_data(self, mock_open):
        mock_open.return_value = _mock_response({"data": "CIPHER"})
        result = self.client.pull("staging")
        self.assertEqual(result, "CIPHER")

    @patch("envoy_cli.remote.urllib.request.urlopen")
    def test_pull_missing_data_raises(self, mock_open):
        mock_open.return_value = _mock_response({"status": "ok"})
        with self.assertRaises(RemoteError):
            self.client.pull("staging")

    # ------------------------------------------------------------------
    # list_profiles
    # ------------------------------------------------------------------

    @patch("envoy_cli.remote.urllib.request.urlopen")
    def test_list_profiles(self, mock_open):
        mock_open.return_value = _mock_response({"profiles": ["dev", "staging"]})
        profiles = self.client.list_profiles()
        self.assertEqual(profiles, ["dev", "staging"])

    # ------------------------------------------------------------------
    # error handling
    # ------------------------------------------------------------------

    @patch("envoy_cli.remote.urllib.request.urlopen")
    def test_http_error_raises_remote_error(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.HTTPError(
            url="https://example.com/envs/x", code=403,
            msg="Forbidden", hdrs=None, fp=None
        )
        with self.assertRaises(RemoteError):
            self.client.pull("x")
