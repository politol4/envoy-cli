"""Tests for envoy_cli.namespace."""

import pytest

from envoy_cli.namespace import (
    NamespaceError,
    keys_in_namespace,
    list_namespaces,
    move_namespace,
    namespace_key,
    split_key,
)


class TestNamespaceKey:
    def test_produces_dotted_key(self):
        assert namespace_key("DB", "HOST") == "DB.HOST"

    def test_empty_namespace_raises(self):
        with pytest.raises(NamespaceError):
            namespace_key("", "HOST")

    def test_empty_key_raises(self):
        with pytest.raises(NamespaceError):
            namespace_key("DB", "")

    def test_namespace_with_dot_raises(self):
        with pytest.raises(NamespaceError):
            namespace_key("DB.PROD", "HOST")


class TestSplitKey:
    def test_splits_namespaced_key(self):
        assert split_key("DB.HOST") == ("DB", "HOST")

    def test_returns_none_ns_for_bare_key(self):
        ns, bare = split_key("HOST")
        assert ns is None
        assert bare == "HOST"

    def test_first_dot_used_as_separator(self):
        ns, bare = split_key("DB.REPLICA.HOST")
        assert ns == "DB"
        assert bare == "REPLICA.HOST"


class TestListNamespaces:
    def test_returns_sorted_unique_namespaces(self):
        secrets = {"DB.HOST": "localhost", "DB.PORT": "5432", "APP.KEY": "secret"}
        assert list_namespaces(secrets) == ["APP", "DB"]

    def test_bare_keys_excluded(self):
        secrets = {"HOST": "localhost", "DB.PORT": "5432"}
        assert list_namespaces(secrets) == ["DB"]

    def test_empty_secrets_returns_empty(self):
        assert list_namespaces({}) == []


class TestKeysInNamespace:
    def test_returns_bare_key_value_pairs(self):
        secrets = {"DB.HOST": "localhost", "DB.PORT": "5432", "APP.KEY": "secret"}
        result = keys_in_namespace(secrets, "DB")
        assert result == {"HOST": "localhost", "PORT": "5432"}

    def test_unknown_namespace_returns_empty(self):
        secrets = {"DB.HOST": "localhost"}
        assert keys_in_namespace(secrets, "APP") == {}

    def test_empty_namespace_raises(self):
        with pytest.raises(NamespaceError):
            keys_in_namespace({}, "")


class TestMoveNamespace:
    def test_keys_renamed(self):
        secrets = {"DB.HOST": "localhost", "DB.PORT": "5432", "APP.KEY": "s"}
        result = move_namespace(secrets, "DB", "PG")
        assert "PG.HOST" in result
        assert "PG.PORT" in result
        assert "DB.HOST" not in result

    def test_other_keys_preserved(self):
        secrets = {"DB.HOST": "localhost", "APP.KEY": "s"}
        result = move_namespace(secrets, "DB", "PG")
        assert "APP.KEY" in result

    def test_values_preserved_after_move(self):
        secrets = {"DB.HOST": "localhost", "DB.PORT": "5432"}
        result = move_namespace(secrets, "DB", "PG")
        assert result["PG.HOST"] == "localhost"
        assert result["PG.PORT"] == "5432"

    def test_same_namespace_raises(self):
        with pytest.raises(NamespaceError):
            move_namespace({"DB.HOST": "x"}, "DB", "DB")

    def test_empty_source_namespace_raises(self):
        with pytest.raises(NamespaceError):
            move_namespace({}, "", "PG")

    def test_empty_destination_namespace_raises(self):
        with pytest.raises(NamespaceError):
            move_namespace({"DB.HOST": "x"}, "DB", "")
