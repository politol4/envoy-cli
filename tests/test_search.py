"""Tests for envoy_cli.search."""

import unittest
from unittest.mock import MagicMock

from envoy_cli.search import SearchError, SearchResult, search_secrets


def _make_vault(secrets: dict) -> MagicMock:
    vault = MagicMock()
    vault.all.return_value = dict(secrets)
    return vault


class TestSearchResult(unittest.TestCase):
    def test_count_reflects_matches(self):
        result = SearchResult(matches={"A": "1", "B": "2"})
        self.assertEqual(result.count, 2)

    def test_has_matches_true(self):
        result = SearchResult(matches={"X": "y"})
        self.assertTrue(result.has_matches)

    def test_has_matches_false_when_empty(self):
        result = SearchResult(matches={})
        self.assertFalse(result.has_matches)

    def test_as_lines_hides_values_by_default(self):
        result = SearchResult(matches={"KEY": "secret"})
        lines = result.as_lines()
        self.assertEqual(lines, ["KEY=***"])

    def test_as_lines_reveals_values_when_requested(self):
        result = SearchResult(matches={"KEY": "secret"})
        lines = result.as_lines(reveal_values=True)
        self.assertEqual(lines, ["KEY=secret"])

    def test_as_lines_sorted_by_key(self):
        result = SearchResult(matches={"ZEBRA": "z", "ALPHA": "a"})
        lines = result.as_lines()
        self.assertEqual(lines[0], "ALPHA=***")
        self.assertEqual(lines[1], "ZEBRA=***")


class TestSearchSecrets(unittest.TestCase):
    def setUp(self):
        self.vault = _make_vault({
            "DB_HOST": "localhost",
            "DB_PASSWORD": "s3cr3t",
            "API_KEY": "abc123",
            "API_SECRET": "xyz789",
        })

    def test_no_pattern_raises(self):
        with self.assertRaises(SearchError):
            search_secrets(self.vault)

    def test_key_glob_pattern_matches(self):
        result = search_secrets(self.vault, key_pattern="DB_*")
        self.assertIn("DB_HOST", result.matches)
        self.assertIn("DB_PASSWORD", result.matches)
        self.assertNotIn("API_KEY", result.matches)

    def test_key_glob_case_insensitive(self):
        result = search_secrets(self.vault, key_pattern="db_*")
        self.assertIn("DB_HOST", result.matches)

    def test_value_glob_pattern_matches(self):
        result = search_secrets(self.vault, value_pattern="*123*")
        self.assertIn("API_KEY", result.matches)
        self.assertNotIn("DB_HOST", result.matches)

    def test_both_patterns_must_match(self):
        result = search_secrets(self.vault, key_pattern="API_*", value_pattern="*123*")
        self.assertIn("API_KEY", result.matches)
        self.assertNotIn("API_SECRET", result.matches)

    def test_regex_key_pattern(self):
        result = search_secrets(self.vault, key_pattern="^DB_", use_regex=True)
        self.assertIn("DB_HOST", result.matches)
        self.assertIn("DB_PASSWORD", result.matches)
        self.assertNotIn("API_KEY", result.matches)

    def test_regex_value_pattern(self):
        result = search_secrets(self.vault, value_pattern="[0-9]+", use_regex=True)
        self.assertIn("API_KEY", result.matches)
        self.assertIn("API_SECRET", result.matches)

    def test_invalid_regex_raises_search_error(self):
        with self.assertRaises(SearchError):
            search_secrets(self.vault, key_pattern="[invalid", use_regex=True)

    def test_no_matches_returns_empty_result(self):
        result = search_secrets(self.vault, key_pattern="NONEXISTENT_*")
        self.assertFalse(result.has_matches)
        self.assertEqual(result.count, 0)

    def test_returns_search_result_instance(self):
        result = search_secrets(self.vault, key_pattern="*")
        self.assertIsInstance(result, SearchResult)


if __name__ == "__main__":
    unittest.main()
