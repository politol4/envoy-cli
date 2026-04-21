"""Tests for envoy_cli.retention."""
from __future__ import annotations

import time
import unittest

from envoy_cli.retention import (
    RetentionError,
    _meta_key,
    set_retention,
    remove_retention,
    get_retention,
    find_expired,
    purge_expired,
    RETENTION_META_PREFIX,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


class TestSetRetention(unittest.TestCase):
    def test_meta_key_added(self):
        result = set_retention(_base(), "DB_URL", 30)
        self.assertIn(_meta_key("DB_URL"), result)

    def test_meta_key_value_contains_days(self):
        result = set_retention(_base(), "DB_URL", 30)
        value = result[_meta_key("DB_URL")]
        days, _ = value.split(":")
        self.assertEqual(int(days), 30)

    def test_original_secrets_unchanged(self):
        result = set_retention(_base(), "DB_URL", 30)
        self.assertEqual(result["DB_URL"], "postgres://localhost/db")
        self.assertEqual(result["API_KEY"], "secret123")

    def test_missing_key_raises(self):
        with self.assertRaises(RetentionError):
            set_retention(_base(), "NONEXISTENT", 30)

    def test_zero_days_raises(self):
        with self.assertRaises(RetentionError):
            set_retention(_base(), "DB_URL", 0)

    def test_negative_days_raises(self):
        with self.assertRaises(RetentionError):
            set_retention(_base(), "DB_URL", -5)

    def test_created_at_is_recent(self):
        before = int(time.time())
        result = set_retention(_base(), "DB_URL", 10)
        after = int(time.time())
        _, ts_str = result[_meta_key("DB_URL")].split(":")
        ts = int(ts_str)
        self.assertGreaterEqual(ts, before)
        self.assertLessEqual(ts, after)


class TestRemoveRetention(unittest.TestCase):
    def test_meta_key_removed(self):
        secrets = set_retention(_base(), "DB_URL", 30)
        result = remove_retention(secrets, "DB_URL")
        self.assertNotIn(_meta_key("DB_URL"), result)

    def test_other_keys_preserved(self):
        secrets = set_retention(_base(), "DB_URL", 30)
        result = remove_retention(secrets, "DB_URL")
        self.assertIn("DB_URL", result)
        self.assertIn("API_KEY", result)

    def test_no_policy_raises(self):
        with self.assertRaises(RetentionError):
            remove_retention(_base(), "DB_URL")


class TestGetRetention(unittest.TestCase):
    def test_returns_none_when_not_set(self):
        self.assertIsNone(get_retention(_base(), "DB_URL"))

    def test_returns_days_and_timestamp(self):
        secrets = set_retention(_base(), "API_KEY", 7)
        info = get_retention(secrets, "API_KEY")
        self.assertIsNotNone(info)
        days, created_at = info
        self.assertEqual(days, 7)
        self.assertIsInstance(created_at, int)


class TestFindExpired(unittest.TestCase):
    def _past_ts(self, days_ago: float) -> int:
        return int(time.time() - days_ago * 86400)

    def _inject_policy(self, secrets: dict, key: str, days: int, created_at: int) -> dict:
        return {**secrets, _meta_key(key): f"{days}:{created_at}"}

    def test_empty_when_no_policies(self):
        self.assertEqual(find_expired(_base()), [])

    def test_not_expired_within_period(self):
        secrets = self._inject_policy(_base(), "DB_URL", 30, self._past_ts(10))
        self.assertEqual(find_expired(secrets), [])

    def test_expired_past_period(self):
        secrets = self._inject_policy(_base(), "DB_URL", 30, self._past_ts(31))
        self.assertIn("DB_URL", find_expired(secrets))

    def test_returns_sorted_list(self):
        secrets = _base()
        secrets = self._inject_policy(secrets, "DB_URL", 1, self._past_ts(2))
        secrets = self._inject_policy(secrets, "API_KEY", 1, self._past_ts(2))
        result = find_expired(secrets)
        self.assertEqual(result, sorted(result))


class TestPurgeExpired(unittest.TestCase):
    def _inject_policy(self, secrets: dict, key: str, days: int, created_at: int) -> dict:
        return {**secrets, _meta_key(key): f"{days}:{created_at}"}

    def test_removes_expired_key_and_meta(self):
        past = int(time.time() - 40 * 86400)
        secrets = self._inject_policy(_base(), "DB_URL", 30, past)
        result = purge_expired(secrets)
        self.assertNotIn("DB_URL", result)
        self.assertNotIn(_meta_key("DB_URL"), result)

    def test_preserves_non_expired_key(self):
        past = int(time.time() - 40 * 86400)
        secrets = self._inject_policy(_base(), "DB_URL", 30, past)
        result = purge_expired(secrets)
        self.assertIn("API_KEY", result)

    def test_no_expired_returns_same_keys(self):
        result = purge_expired(_base())
        self.assertEqual(set(result.keys()), set(_base().keys()))


if __name__ == "__main__":
    unittest.main()
