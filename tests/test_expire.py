"""Tests for envoy_cli.expire."""
import time
import tempfile
import os
import unittest

from envoy_cli.vault import Vault
from envoy_cli.expire import find_expired, purge_expired, ExpireResult

_PASS = "test-pass"


def _make_vault(secrets: dict) -> Vault:
    v = Vault()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".vault") as f:
        path = f.name
    v.load(path, _PASS)  # initialises empty vault
    for k, val in secrets.items():
        v.set(k, val)
    return v


class TestExpireResult(unittest.TestCase):
    def test_has_expired_false_when_empty(self):
        r = ExpireResult()
        self.assertFalse(r.has_expired)

    def test_has_expired_true_when_keys_present(self):
        r = ExpireResult(expired=["FOO"])
        self.assertTrue(r.has_expired)

    def test_summary_no_expired(self):
        r = ExpireResult()
        self.assertIn("No expired", r.summary())

    def test_summary_lists_keys(self):
        r = ExpireResult(expired=["BAR", "FOO"])
        summary = r.summary()
        self.assertIn("FOO", summary)
        self.assertIn("BAR", summary)
        self.assertIn("2", summary)


class TestFindExpired(unittest.TestCase):
    def test_no_ttl_keys_all_retained(self):
        v = _make_vault({"KEY": "val"})
        result = find_expired(v)
        self.assertFalse(result.has_expired)
        self.assertIn("KEY", result.retained)

    def test_future_ttl_retained(self):
        future = str(time.time() + 9999)
        v = _make_vault({"KEY": "val", "__ttl__KEY": future})
        result = find_expired(v)
        self.assertNotIn("KEY", result.expired)
        self.assertIn("KEY", result.retained)

    def test_past_ttl_expired(self):
        past = str(time.time() - 1)
        v = _make_vault({"KEY": "val", "__ttl__KEY": past})
        result = find_expired(v)
        self.assertIn("KEY", result.expired)
        self.assertNotIn("KEY", result.retained)

    def test_meta_keys_not_in_retained_or_expired(self):
        past = str(time.time() - 1)
        v = _make_vault({"KEY": "val", "__ttl__KEY": past})
        result = find_expired(v)
        self.assertNotIn("__ttl__KEY", result.expired)
        self.assertNotIn("__ttl__KEY", result.retained)

    def test_invalid_ttl_value_treated_as_retained(self):
        v = _make_vault({"KEY": "val", "__ttl__KEY": "not-a-float"})
        result = find_expired(v)
        self.assertIn("KEY", result.retained)


class TestPurgeExpired(unittest.TestCase):
    def test_expired_key_removed_from_vault(self):
        past = str(time.time() - 1)
        v = _make_vault({"KEY": "val", "__ttl__KEY": past})
        purge_expired(v)
        self.assertIsNone(v.get("KEY"))

    def test_retained_key_still_present(self):
        future = str(time.time() + 9999)
        past = str(time.time() - 1)
        v = _make_vault({
            "KEEP": "yes", "__ttl__KEEP": future,
            "DROP": "no", "__ttl__DROP": past,
        })
        result = purge_expired(v)
        self.assertIn("DROP", result.expired)
        self.assertEqual(v.get("KEEP"), "yes")

    def test_returns_expire_result(self):
        past = str(time.time() - 1)
        v = _make_vault({"X": "1", "__ttl__X": past})
        result = purge_expired(v)
        self.assertIsInstance(result, ExpireResult)
        self.assertIn("X", result.expired)

    def test_no_expired_returns_empty_result(self):
        v = _make_vault({"KEY": "val"})
        result = purge_expired(v)
        self.assertFalse(result.has_expired)


if __name__ == "__main__":
    unittest.main()
