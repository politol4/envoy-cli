"""Tests for envoy_cli.ttl."""

from __future__ import annotations

import time
import unittest

from envoy_cli.ttl import (
    TTLError,
    _meta_key,
    get_ttl,
    list_expiring,
    purge_expired,
    remove_ttl,
    set_ttl,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


class TestSetTTL(unittest.TestCase):
    def test_meta_key_added(self):
        result = set_ttl(_base(), "DB_URL", 60)
        self.assertIn(_meta_key("DB_URL"), result)

    def test_expiry_is_in_future(self):
        result = set_ttl(_base(), "DB_URL", 60)
        expiry = int(result[_meta_key("DB_URL")])
        self.assertGreater(expiry, int(time.time()))

    def test_missing_key_raises(self):
        with self.assertRaises(TTLError):
            set_ttl(_base(), "MISSING_KEY", 60)

    def test_zero_seconds_raises(self):
        with self.assertRaises(TTLError):
            set_ttl(_base(), "DB_URL", 0)

    def test_negative_seconds_raises(self):
        with self.assertRaises(TTLError):
            set_ttl(_base(), "DB_URL", -10)

    def test_original_secrets_unchanged(self):
        original = _base()
        set_ttl(original, "DB_URL", 60)
        self.assertNotIn(_meta_key("DB_URL"), original)


class TestGetTTL(unittest.TestCase):
    def test_returns_none_when_no_ttl(self):
        self.assertIsNone(get_ttl(_base(), "DB_URL"))

    def test_returns_positive_remaining(self):
        secrets = set_ttl(_base(), "DB_URL", 300)
        remaining = get_ttl(secrets, "DB_URL")
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, 300)

    def test_returns_zero_for_expired(self):
        secrets = dict(_base())
        secrets[_meta_key("DB_URL")] = str(int(time.time()) - 10)
        self.assertEqual(get_ttl(secrets, "DB_URL"), 0)


class TestRemoveTTL(unittest.TestCase):
    def test_meta_key_gone_after_remove(self):
        secrets = set_ttl(_base(), "API_KEY", 60)
        result = remove_ttl(secrets, "API_KEY")
        self.assertNotIn(_meta_key("API_KEY"), result)

    def test_remove_noop_when_no_ttl(self):
        result = remove_ttl(_base(), "DB_URL")
        self.assertEqual(result["DB_URL"], "postgres://localhost/db")


class TestPurgeExpired(unittest.TestCase):
    def _expired_secrets(self):
        secrets = dict(_base())
        secrets[_meta_key("DB_URL")] = str(int(time.time()) - 5)
        return secrets

    def test_expired_key_removed(self):
        result = purge_expired(self._expired_secrets())
        self.assertNotIn("DB_URL", result)

    def test_expired_meta_key_removed(self):
        result = purge_expired(self._expired_secrets())
        self.assertNotIn(_meta_key("DB_URL"), result)

    def test_non_expired_key_kept(self):
        secrets = self._expired_secrets()
        secrets = set_ttl(secrets, "API_KEY", 300)
        result = purge_expired(secrets)
        self.assertIn("API_KEY", result)

    def test_no_ttl_key_kept(self):
        result = purge_expired(_base())
        self.assertEqual(result["DB_URL"], "postgres://localhost/db")


class TestListExpiring(unittest.TestCase):
    def test_returns_key_expiring_soon(self):
        secrets = set_ttl(_base(), "DB_URL", 30)
        result = list_expiring(secrets, within_seconds=60)
        self.assertIn("DB_URL", result)

    def test_excludes_key_not_expiring_soon(self):
        secrets = set_ttl(_base(), "DB_URL", 7200)
        result = list_expiring(secrets, within_seconds=60)
        self.assertNotIn("DB_URL", result)

    def test_excludes_keys_with_no_ttl(self):
        result = list_expiring(_base(), within_seconds=9999)
        self.assertEqual(result, [])

    def test_result_is_sorted(self):
        secrets = set_ttl(_base(), "DB_URL", 10)
        secrets = set_ttl(secrets, "API_KEY", 20)
        result = list_expiring(secrets, within_seconds=60)
        self.assertEqual(result, sorted(result))
