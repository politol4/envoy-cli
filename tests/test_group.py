"""Tests for envoy_cli.group."""

import pytest

from envoy_cli.group import (
    GROUP_PREFIX,
    GroupError,
    _meta_key,
    create_group,
    delete_group,
    get_group_keys,
    get_group_secrets,
    list_groups,
)


def _base() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}


class TestCreateGroup:
    def test_meta_key_added(self):
        result = create_group(_base(), "db", ["DB_HOST", "DB_PORT"])
        assert _meta_key("db") in result

    def test_meta_key_value_contains_keys(self):
        result = create_group(_base(), "db", ["DB_HOST", "DB_PORT"])
        stored = result[_meta_key("db")]
        assert "DB_HOST" in stored
        assert "DB_PORT" in stored

    def test_original_secrets_unchanged(self):
        result = create_group(_base(), "db", ["DB_HOST"])
        assert result["DB_HOST"] == "localhost"

    def test_empty_name_raises(self):
        with pytest.raises(GroupError, match="empty"):
            create_group(_base(), "", ["DB_HOST"])

    def test_missing_key_raises(self):
        with pytest.raises(GroupError, match="not found"):
            create_group(_base(), "db", ["MISSING_KEY"])

    def test_duplicate_keys_deduplicated(self):
        result = create_group(_base(), "db", ["DB_HOST", "DB_HOST"])
        stored = result[_meta_key("db")]
        assert stored.count("DB_HOST") == 1

    def test_overwrite_existing_group(self):
        first = create_group(_base(), "db", ["DB_HOST"])
        second = create_group(first, "db", ["DB_PORT"])
        assert "DB_PORT" in second[_meta_key("db")]
        assert "DB_HOST" not in second[_meta_key("db")]


class TestDeleteGroup:
    def test_meta_key_removed(self):
        secrets = create_group(_base(), "db", ["DB_HOST"])
        result = delete_group(secrets, "db")
        assert _meta_key("db") not in result

    def test_member_keys_preserved(self):
        secrets = create_group(_base(), "db", ["DB_HOST"])
        result = delete_group(secrets, "db")
        assert result["DB_HOST"] == "localhost"

    def test_nonexistent_group_raises(self):
        with pytest.raises(GroupError, match="does not exist"):
            delete_group(_base(), "nonexistent")


class TestGetGroupKeys:
    def test_returns_member_keys(self):
        secrets = create_group(_base(), "db", ["DB_HOST", "DB_PORT"])
        keys = get_group_keys(secrets, "db")
        assert set(keys) == {"DB_HOST", "DB_PORT"}

    def test_nonexistent_group_raises(self):
        with pytest.raises(GroupError, match="does not exist"):
            get_group_keys(_base(), "missing")


class TestListGroups:
    def test_returns_sorted_group_names(self):
        s = create_group(_base(), "zgroup", ["DB_HOST"])
        s = create_group(s, "agroup", ["DB_PORT"])
        groups = list_groups(s)
        assert groups == ["agroup", "zgroup"]

    def test_empty_vault_returns_empty_list(self):
        assert list_groups({}) == []

    def test_normal_keys_not_included(self):
        groups = list_groups(_base())
        assert groups == []


class TestGetGroupSecrets:
    def test_returns_key_value_pairs(self):
        secrets = create_group(_base(), "db", ["DB_HOST", "DB_PORT"])
        members = get_group_secrets(secrets, "db")
        assert members == {"DB_HOST": "localhost", "DB_PORT": "5432"}

    def test_missing_member_raises(self):
        secrets = create_group(_base(), "db", ["DB_HOST"])
        del secrets["DB_HOST"]
        with pytest.raises(GroupError, match="missing from vault"):
            get_group_secrets(secrets, "db")
