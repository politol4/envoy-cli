"""Tests for envoy_cli.redact."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from envoy_cli.redact import (
    REDACTED_PLACEHOLDER,
    RedactError,
    _collect_values,
    redact_from_vault,
    redact_text,
)


SECRETS = {
    "DB_PASSWORD": "supersecret",
    "API_KEY": "abc123xyz",
    "SHORT": "ab",  # below minimum length — should not be replaced
}


class TestCollectValues(unittest.TestCase):
    def test_excludes_short_values(self):
        values = _collect_values(SECRETS)
        self.assertNotIn("ab", values)

    def test_sorted_longest_first(self):
        values = _collect_values(SECRETS)
        lengths = [len(v) for v in values]
        self.assertEqual(lengths, sorted(lengths, reverse=True))

    def test_empty_secrets_returns_empty(self):
        self.assertEqual(_collect_values({}), [])


class TestRedactText(unittest.TestCase):
    def test_replaces_single_secret(self):
        result = redact_text("password is supersecret ok", SECRETS)
        self.assertIn(REDACTED_PLACEHOLDER, result)
        self.assertNotIn("supersecret", result)

    def test_replaces_multiple_secrets(self):
        text = "key=abc123xyz pass=supersecret"
        result = redact_text(text, SECRETS)
        self.assertNotIn("abc123xyz", result)
        self.assertNotIn("supersecret", result)

    def test_short_value_not_replaced(self):
        result = redact_text("ab is here", SECRETS)
        self.assertIn("ab", result)

    def test_empty_text_returns_empty(self):
        self.assertEqual(redact_text("", SECRETS), "")

    def test_no_secrets_returns_original(self):
        text = "nothing sensitive"
        self.assertEqual(redact_text(text, {}), text)

    def test_multiple_occurrences_all_replaced(self):
        text = "supersecret supersecret"
        result = redact_text(text, SECRETS)
        self.assertEqual(result, f"{REDACTED_PLACEHOLDER} {REDACTED_PLACEHOLDER}")

    def test_placeholder_not_double_redacted(self):
        # If placeholder itself appears in text it should survive intact.
        text = f"value={REDACTED_PLACEHOLDER}"
        result = redact_text(text, SECRETS)
        self.assertIn(REDACTED_PLACEHOLDER, result)


class TestRedactFromVault(unittest.TestCase):
    def _make_vault(self, secrets):
        vault = MagicMock()
        vault.get_all.return_value = secrets
        return vault

    def test_delegates_to_redact_text(self):
        vault = self._make_vault({"TOKEN": "mytoken123"})
        result = redact_from_vault("token=mytoken123", vault, "pass", "dev")
        self.assertNotIn("mytoken123", result)
        self.assertIn(REDACTED_PLACEHOLDER, result)

    def test_missing_env_raises(self):
        vault = self._make_vault(None)
        with self.assertRaises(RedactError):
            redact_from_vault("some text", vault, "pass", "missing")

    def test_vault_get_all_called_with_env_and_passphrase(self):
        vault = self._make_vault({"K": "value123"})
        redact_from_vault("value123", vault, "mypass", "staging")
        vault.get_all.assert_called_once_with("staging", "mypass")


if __name__ == "__main__":
    unittest.main()
