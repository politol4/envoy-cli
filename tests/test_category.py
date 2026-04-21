"""Tests for envoy_cli.category."""

import pytest

from envoy_cli.category import (
    CategoryError,
    get_category,
    list_by_category,
    remove_category,
    set_category,
    _meta_key,
)


def _base() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}


class TestSetCategory:
    def test_meta_key_added(self):
        result = set_category(_base(), "DB_HOST", "database")
        assert _meta_key("DB_HOST") in result

    def test_meta_key_value_is_category(self):
        result = set_category(_base(), "DB_HOST", "database")
        assert result[_meta_key("DB_HOST")] == "database"

    def test_original_secrets_unchanged(self):
        base = _base()
        result = set_category(base, "DB_HOST", "database")
        assert result["DB_HOST"] == base["DB_HOST"]

    def test_missing_key_raises(self):
        with pytest.raises(CategoryError, match="key not found"):
            set_category(_base(), "MISSING", "database")

    def test_empty_category_raises(self):
        with pytest.raises(CategoryError, match="must not be empty"):
            set_category(_base(), "DB_HOST", "")

    def test_whitespace_only_category_raises(self):
        with pytest.raises(CategoryError, match="must not be empty"):
            set_category(_base(), "DB_HOST", "   ")

    def test_category_is_stripped(self):
        result = set_category(_base(), "DB_HOST", "  infra  ")
        assert result[_meta_key("DB_HOST")] == "infra"

    def test_original_dict_not_mutated(self):
        base = _base()
        set_category(base, "DB_HOST", "database")
        assert _meta_key("DB_HOST") not in base


class TestRemoveCategory:
    def test_meta_key_removed(self):
        secrets = set_category(_base(), "DB_HOST", "database")
        result = remove_category(secrets, "DB_HOST")
        assert _meta_key("DB_HOST") not in result

    def test_original_value_preserved(self):
        secrets = set_category(_base(), "DB_HOST", "database")
        result = remove_category(secrets, "DB_HOST")
        assert result["DB_HOST"] == "localhost"

    def test_no_category_raises(self):
        with pytest.raises(CategoryError, match="no category set"):
            remove_category(_base(), "DB_HOST")


class TestGetCategory:
    def test_returns_category_when_set(self):
        secrets = set_category(_base(), "API_KEY", "auth")
        assert get_category(secrets, "API_KEY") == "auth"

    def test_returns_none_when_unset(self):
        assert get_category(_base(), "DB_HOST") is None


class TestListByCategory:
    def test_empty_secrets_returns_empty(self):
        assert list_by_category({}) == {}

    def test_no_categories_returns_empty(self):
        assert list_by_category(_base()) == {}

    def test_single_category(self):
        secrets = set_category(_base(), "DB_HOST", "database")
        secrets = set_category(secrets, "DB_PORT", "database")
        result = list_by_category(secrets)
        assert result == {"database": ["DB_HOST", "DB_PORT"]}

    def test_multiple_categories(self):
        secrets = set_category(_base(), "DB_HOST", "database")
        secrets = set_category(secrets, "API_KEY", "auth")
        result = list_by_category(secrets)
        assert "database" in result
        assert "auth" in result
        assert result["database"] == ["DB_HOST"]
        assert result["auth"] == ["API_KEY"]

    def test_keys_sorted_within_category(self):
        base = {"Z_KEY": "z", "A_KEY": "a", "M_KEY": "m"}
        secrets = set_category(base, "Z_KEY", "group")
        secrets = set_category(secrets, "A_KEY", "group")
        secrets = set_category(secrets, "M_KEY", "group")
        result = list_by_category(secrets)
        assert result["group"] == ["A_KEY", "M_KEY", "Z_KEY"]
