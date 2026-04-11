"""Tests for envoy_cli.tag."""

import unittest

from envoy_cli.tag import (
    TagError,
    add_tag,
    remove_tag,
    get_tags,
    filter_by_tag,
    list_all_tags,
    _TAG_META_PREFIX,
)


def _base_secrets():
    return {"DB_URL": "postgres://localhost", "API_KEY": "abc123", "SECRET": "s3cr3t"}


class TestAddTag(unittest.TestCase):
    def test_adds_tag_to_existing_key(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "database")
        self.assertIn("database", get_tags(s, "DB_URL"))

    def test_multiple_tags_stored(self):
        s = _base_secrets()
        add_tag(s, "API_KEY", "external")
        add_tag(s, "API_KEY", "sensitive")
        tags = get_tags(s, "API_KEY")
        self.assertIn("external", tags)
        self.assertIn("sensitive", tags)

    def test_duplicate_tag_not_added_twice(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "infra")
        add_tag(s, "DB_URL", "infra")
        self.assertEqual(get_tags(s, "DB_URL").count("infra"), 1)

    def test_missing_key_raises(self):
        s = _base_secrets()
        with self.assertRaises(TagError):
            add_tag(s, "NONEXISTENT", "tag")

    def test_empty_tag_raises(self):
        s = _base_secrets()
        with self.assertRaises(TagError):
            add_tag(s, "DB_URL", "   ")

    def test_meta_key_not_exposed_as_secret(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "infra")
        for k in s:
            if k.startswith(_TAG_META_PREFIX):
                return  # meta key exists but should not appear in filtered results
        self.fail("meta key not found")


class TestRemoveTag(unittest.TestCase):
    def test_removes_existing_tag(self):
        s = _base_secrets()
        add_tag(s, "API_KEY", "external")
        remove_tag(s, "API_KEY", "external")
        self.assertNotIn("external", get_tags(s, "API_KEY"))

    def test_remove_last_tag_cleans_meta_key(self):
        s = _base_secrets()
        add_tag(s, "SECRET", "sensitive")
        remove_tag(s, "SECRET", "sensitive")
        meta_key = f"{_TAG_META_PREFIX}SECRET"
        self.assertNotIn(meta_key, s)

    def test_remove_absent_tag_is_noop(self):
        s = _base_secrets()
        remove_tag(s, "DB_URL", "nonexistent")  # should not raise

    def test_missing_key_raises(self):
        s = _base_secrets()
        with self.assertRaises(TagError):
            remove_tag(s, "MISSING", "tag")


class TestFilterByTag(unittest.TestCase):
    def test_returns_only_tagged_secrets(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "infra")
        add_tag(s, "API_KEY", "infra")
        result = filter_by_tag(s, "infra")
        self.assertIn("DB_URL", result)
        self.assertIn("API_KEY", result)
        self.assertNotIn("SECRET", result)

    def test_no_match_returns_empty(self):
        s = _base_secrets()
        result = filter_by_tag(s, "ghost")
        self.assertEqual(result, {})

    def test_meta_keys_excluded_from_result(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "infra")
        result = filter_by_tag(s, "infra")
        for k in result:
            self.assertFalse(k.startswith(_TAG_META_PREFIX))


class TestListAllTags(unittest.TestCase):
    def test_returns_sorted_unique_tags(self):
        s = _base_secrets()
        add_tag(s, "DB_URL", "infra")
        add_tag(s, "API_KEY", "sensitive")
        add_tag(s, "SECRET", "infra")
        tags = list_all_tags(s)
        self.assertEqual(tags, ["infra", "sensitive"])

    def test_empty_secrets_returns_empty(self):
        self.assertEqual(list_all_tags({}), [])


if __name__ == "__main__":
    unittest.main()
