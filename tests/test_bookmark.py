"""Tests for envoy_cli.bookmark."""
import pytest

from envoy_cli.bookmark import (
    BOOKMARK_META_PREFIX,
    BookmarkError,
    _meta_key,
    add_bookmark,
    is_bookmarked,
    list_bookmarks,
    remove_bookmark,
)


def _base():
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


class TestAddBookmark:
    def test_meta_key_added(self):
        result = add_bookmark(_base(), "DB_URL")
        assert _meta_key("DB_URL") in result

    def test_note_stored_correctly(self):
        result = add_bookmark(_base(), "DB_URL", note="primary database")
        assert result[_meta_key("DB_URL")] == "primary database"

    def test_empty_note_stored_as_empty_string(self):
        result = add_bookmark(_base(), "API_KEY")
        assert result[_meta_key("API_KEY")] == ""

    def test_original_secrets_unchanged(self):
        base = _base()
        result = add_bookmark(base, "DB_URL")
        assert result["DB_URL"] == base["DB_URL"]
        assert result["API_KEY"] == base["API_KEY"]

    def test_missing_key_raises(self):
        with pytest.raises(BookmarkError, match="MISSING"):
            add_bookmark(_base(), "MISSING")

    def test_does_not_mutate_input(self):
        base = _base()
        add_bookmark(base, "DB_URL")
        assert _meta_key("DB_URL") not in base


class TestRemoveBookmark:
    def test_meta_key_removed(self):
        secrets = add_bookmark(_base(), "DB_URL", note="test")
        result = remove_bookmark(secrets, "DB_URL")
        assert _meta_key("DB_URL") not in result

    def test_original_key_preserved(self):
        secrets = add_bookmark(_base(), "DB_URL")
        result = remove_bookmark(secrets, "DB_URL")
        assert "DB_URL" in result

    def test_not_bookmarked_raises(self):
        with pytest.raises(BookmarkError, match="not bookmarked"):
            remove_bookmark(_base(), "DB_URL")

    def test_does_not_mutate_input(self):
        secrets = add_bookmark(_base(), "API_KEY")
        original_len = len(secrets)
        remove_bookmark(secrets, "API_KEY")
        assert len(secrets) == original_len


class TestIsBookmarked:
    def test_returns_true_when_bookmarked(self):
        secrets = add_bookmark(_base(), "DB_URL")
        assert is_bookmarked(secrets, "DB_URL") is True

    def test_returns_false_when_not_bookmarked(self):
        assert is_bookmarked(_base(), "DB_URL") is False

    def test_returns_false_after_removal(self):
        secrets = add_bookmark(_base(), "API_KEY")
        secrets = remove_bookmark(secrets, "API_KEY")
        assert is_bookmarked(secrets, "API_KEY") is False


class TestListBookmarks:
    def test_empty_when_no_bookmarks(self):
        assert list_bookmarks(_base()) == []

    def test_returns_bookmarked_keys(self):
        secrets = add_bookmark(_base(), "DB_URL", note="db")
        secrets = add_bookmark(secrets, "API_KEY", note="key")
        result = list_bookmarks(secrets)
        keys = [e["key"] for e in result]
        assert "DB_URL" in keys
        assert "API_KEY" in keys

    def test_sorted_alphabetically(self):
        secrets = add_bookmark(_base(), "DB_URL")
        secrets = add_bookmark(secrets, "API_KEY")
        result = list_bookmarks(secrets)
        assert result[0]["key"] == "API_KEY"
        assert result[1]["key"] == "DB_URL"

    def test_note_included_in_result(self):
        secrets = add_bookmark(_base(), "DB_URL", note="main db")
        result = list_bookmarks(secrets)
        assert result[0]["note"] == "main db"

    def test_meta_keys_not_listed_as_bookmarks(self):
        secrets = add_bookmark(_base(), "DB_URL")
        result = list_bookmarks(secrets)
        for entry in result:
            assert not entry["key"].startswith(BOOKMARK_META_PREFIX)
