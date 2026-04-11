"""Tests for envoy_cli.alias."""

import pytest

from envoy_cli.alias import (
    ALIAS_PREFIX,
    AliasError,
    add_alias,
    list_aliases,
    remove_alias,
    resolve_alias,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost/dev", "API_KEY": "secret123"}


class TestAddAlias:
    def test_meta_key_added(self):
        result = add_alias(_base(), "database", "DB_URL")
        assert f"{ALIAS_PREFIX}database" in result

    def test_meta_key_value_is_target(self):
        result = add_alias(_base(), "database", "DB_URL")
        assert result[f"{ALIAS_PREFIX}database"] == "DB_URL"

    def test_original_secrets_unchanged(self):
        base = _base()
        result = add_alias(base, "database", "DB_URL")
        assert result["DB_URL"] == base["DB_URL"]

    def test_missing_target_raises(self):
        with pytest.raises(AliasError, match="does not exist"):
            add_alias(_base(), "missing", "NO_SUCH_KEY")

    def test_empty_alias_raises(self):
        with pytest.raises(AliasError, match="must not be empty"):
            add_alias(_base(), "", "DB_URL")

    def test_empty_target_raises(self):
        with pytest.raises(AliasError, match="must not be empty"):
            add_alias(_base(), "db", "")

    def test_alias_conflicts_with_real_key_raises(self):
        with pytest.raises(AliasError, match="real secret key"):
            add_alias(_base(), "DB_URL", "API_KEY")

    def test_reassigning_same_target_is_idempotent(self):
        first = add_alias(_base(), "db", "DB_URL")
        second = add_alias(first, "db", "DB_URL")
        assert second[f"{ALIAS_PREFIX}db"] == "DB_URL"

    def test_reassigning_different_target_raises(self):
        first = add_alias(_base(), "db", "DB_URL")
        with pytest.raises(AliasError, match="already points to"):
            add_alias(first, "db", "API_KEY")


class TestRemoveAlias:
    def test_meta_key_removed(self):
        secrets = add_alias(_base(), "db", "DB_URL")
        result = remove_alias(secrets, "db")
        assert f"{ALIAS_PREFIX}db" not in result

    def test_target_key_still_present(self):
        secrets = add_alias(_base(), "db", "DB_URL")
        result = remove_alias(secrets, "db")
        assert "DB_URL" in result

    def test_removing_nonexistent_alias_raises(self):
        with pytest.raises(AliasError, match="not registered"):
            remove_alias(_base(), "ghost")


class TestResolveAlias:
    def test_returns_target_value(self):
        secrets = add_alias(_base(), "db", "DB_URL")
        assert resolve_alias(secrets, "db") == _base()["DB_URL"]

    def test_unregistered_alias_raises(self):
        with pytest.raises(AliasError, match="not registered"):
            resolve_alias(_base(), "nope")

    def test_dangling_alias_raises(self):
        secrets = add_alias(_base(), "db", "DB_URL")
        del secrets["DB_URL"]  # simulate key deletion without removing alias
        with pytest.raises(AliasError, match="no longer exists"):
            resolve_alias(secrets, "db")


class TestListAliases:
    def test_empty_when_no_aliases(self):
        assert list_aliases(_base()) == []

    def test_returns_alias_and_target(self):
        secrets = add_alias(_base(), "db", "DB_URL")
        entries = list_aliases(secrets)
        assert entries == [{"alias": "db", "target": "DB_URL"}]

    def test_sorted_by_alias_name(self):
        secrets = add_alias(_base(), "zz", "DB_URL")
        secrets = add_alias(secrets, "aa", "API_KEY")
        names = [e["alias"] for e in list_aliases(secrets)]
        assert names == ["aa", "zz"]
