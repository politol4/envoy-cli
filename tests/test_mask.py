"""Tests for envoy_cli.mask."""

from __future__ import annotations

import unittest

from envoy_cli.mask import mask_value, mask_secrets, reveal_preview, MaskError


class TestMaskValue(unittest.TestCase):
    def test_long_value_shows_prefix(self):
        result = mask_value("ABCDEFGH")
        self.assertTrue(result.startswith("ABCD"))

    def test_long_value_rest_is_stars(self):
        result = mask_value("ABCDEFGH")
        self.assertEqual(result, "ABCD****")

    def test_short_value_fully_masked(self):
        # shorter than _MIN_LENGTH_TO_PARTIAL → all stars, at least 4
        result = mask_value("abc")
        self.assertTrue(all(c == "*" for c in result))
        self.assertGreaterEqual(len(result), 4)

    def test_custom_visible(self):
        result = mask_value("ABCDEFGHIJ", visible=2)
        self.assertTrue(result.startswith("AB"))
        self.assertEqual(result[2:], "*" * 8)

    def test_non_string_raises(self):
        with self.assertRaises(MaskError):
            mask_value(12345)  # type: ignore[arg-type]

    def test_empty_string_fully_masked(self):
        result = mask_value("")
        self.assertEqual(result, "****")


class TestMaskSecrets(unittest.TestCase):
    def _secrets(self):
        return {"DB_PASS": "supersecret", "API_KEY": "keyvalue123"}

    def test_all_values_masked(self):
        masked = mask_secrets(self._secrets())
        for val in masked.values():
            self.assertIn("*", val)

    def test_keys_preserved(self):
        masked = mask_secrets(self._secrets())
        self.assertSetEqual(set(masked.keys()), {"DB_PASS", "API_KEY"})

    def test_meta_keys_skipped(self):
        secrets = {"__tags__DB_PASS": "production", "DB_PASS": "supersecret"}
        masked = mask_secrets(secrets)
        self.assertEqual(masked["__tags__DB_PASS"], "production")
        self.assertIn("*", masked["DB_PASS"])

    def test_explicit_skip_keys_passed_through(self):
        secrets = {"PUBLIC_URL": "https://example.com", "SECRET": "s3cr3tvalue"}
        masked = mask_secrets(secrets, skip_keys=["PUBLIC_URL"])
        self.assertEqual(masked["PUBLIC_URL"], "https://example.com")
        self.assertIn("*", masked["SECRET"])

    def test_empty_dict_returns_empty(self):
        self.assertEqual(mask_secrets({}), {})


class TestRevealPreview(unittest.TestCase):
    def test_returns_masked_string(self):
        preview = reveal_preview("ABCDEFGHIJ")
        self.assertTrue(preview.startswith("ABCD"))

    def test_custom_visible_length(self):
        preview = reveal_preview("ABCDEFGHIJ", visible=2)
        self.assertTrue(preview.startswith("AB"))


if __name__ == "__main__":
    unittest.main()
