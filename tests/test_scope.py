"""Tests for envoy_cli/scope.py"""
import pytest

from envoy_cli.scope import (
    ScopeError,
    get_scope,
    keys_in_scope,
    list_scopes,
    remove_scope,
    set_scope,
)


def _base() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}


# ---------------------------------------------------------------------------
# set_scope
# ---------------------------------------------------------------------------

class TestSetScope:
    def test_meta_key_added(self):
        result = set_scope(_base(), "DB_HOST", "backend")
        assert "__scope__DB_HOST" in result

    def test_meta_key_value_is_scope(self):
        result = set_scope(_base(), "DB_HOST", "backend")
        assert result["__scope__DB_HOST"] == "backend"

    def test_original_secrets_unchanged(self):
        base = _base()
        result = set_scope(base, "DB_HOST", "backend")
        assert result["DB_HOST"] == "localhost"

    def test_missing_key_raises(self):
        with pytest.raises(ScopeError, match="not found"):
            set_scope(_base(), "MISSING", "backend")

    def test_empty_key_raises(self):
        with pytest.raises(ScopeError, match="key must not be empty"):
            set_scope(_base(), "", "backend")

    def test_empty_scope_raises(self):
        with pytest.raises(ScopeError, match="scope must not be empty"):
            set_scope(_base(), "DB_HOST", "")

    def test_overwrite_existing_scope(self):
        s = set_scope(_base(), "DB_HOST", "backend")
        s = set_scope(s, "DB_HOST", "frontend")
        assert s["__scope__DB_HOST"] == "frontend"


# ---------------------------------------------------------------------------
# remove_scope
# ---------------------------------------------------------------------------

class TestRemoveScope:
    def test_meta_key_removed(self):
        s = set_scope(_base(), "DB_HOST", "backend")
        s = remove_scope(s, "DB_HOST")
        assert "__scope__DB_HOST" not in s

    def test_original_key_preserved(self):
        s = set_scope(_base(), "DB_HOST", "backend")
        s = remove_scope(s, "DB_HOST")
        assert s["DB_HOST"] == "localhost"

    def test_no_scope_raises(self):
        with pytest.raises(ScopeError, match="no scope assigned"):
            remove_scope(_base(), "DB_HOST")


# ---------------------------------------------------------------------------
# get_scope
# ---------------------------------------------------------------------------

class TestGetScope:
    def test_returns_scope_after_set(self):
        s = set_scope(_base(), "API_KEY", "shared")
        assert get_scope(s, "API_KEY") == "shared"

    def test_returns_none_when_not_set(self):
        assert get_scope(_base(), "DB_HOST") is None


# ---------------------------------------------------------------------------
# keys_in_scope
# ---------------------------------------------------------------------------

class TestKeysInScope:
    def _scoped(self):
        s = _base()
        s = set_scope(s, "DB_HOST", "backend")
        s = set_scope(s, "DB_PORT", "backend")
        s = set_scope(s, "API_KEY", "shared")
        return s

    def test_returns_keys_for_scope(self):
        assert keys_in_scope(self._scoped(), "backend") == ["DB_HOST", "DB_PORT"]

    def test_returns_sorted_list(self):
        result = keys_in_scope(self._scoped(), "backend")
        assert result == sorted(result)

    def test_no_match_returns_empty(self):
        assert keys_in_scope(self._scoped(), "nonexistent") == []

    def test_empty_scope_raises(self):
        with pytest.raises(ScopeError, match="scope must not be empty"):
            keys_in_scope(self._scoped(), "")

    def test_meta_keys_excluded(self):
        s = self._scoped()
        for k in keys_in_scope(s, "backend"):
            assert not k.startswith("__scope__")


# ---------------------------------------------------------------------------
# list_scopes
# ---------------------------------------------------------------------------

class TestListScopes:
    def test_returns_unique_scopes(self):
        s = _base()
        s = set_scope(s, "DB_HOST", "backend")
        s = set_scope(s, "DB_PORT", "backend")
        s = set_scope(s, "API_KEY", "shared")
        assert list_scopes(s) == ["backend", "shared"]

    def test_empty_when_no_scopes(self):
        assert list_scopes(_base()) == []

    def test_returns_sorted(self):
        s = _base()
        s = set_scope(s, "DB_HOST", "zebra")
        s = set_scope(s, "API_KEY", "alpha")
        result = list_scopes(s)
        assert result == sorted(result)
