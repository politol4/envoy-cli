"""Tests for envoy_cli/access.py"""
import pytest
from envoy_cli.access import (
    set_access,
    remove_access,
    get_access,
    check_access,
    list_user_keys,
    AccessError,
    ACCESS_META_PREFIX,
)


def _base():
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret123"}


class TestSetAccess:
    def test_meta_key_added(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        assert f"{ACCESS_META_PREFIX}DB_URL" in s

    def test_role_stored_correctly(self):
        s = set_access(_base(), "DB_URL", "write", "bob")
        acl = get_access(s, "DB_URL")
        assert acl["bob"] == "write"

    def test_multiple_users_stored(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = set_access(s, "DB_URL", "admin", "bob")
        acl = get_access(s, "DB_URL")
        assert acl["alice"] == "read"
        assert acl["bob"] == "admin"

    def test_update_existing_user_role(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = set_access(s, "DB_URL", "admin", "alice")
        acl = get_access(s, "DB_URL")
        assert acl["alice"] == "admin"

    def test_missing_key_raises(self):
        with pytest.raises(AccessError, match="not found"):
            set_access(_base(), "MISSING", "read", "alice")

    def test_invalid_role_raises(self):
        with pytest.raises(AccessError, match="Invalid role"):
            set_access(_base(), "DB_URL", "superuser", "alice")

    def test_empty_user_raises(self):
        with pytest.raises(AccessError, match="non-empty"):
            set_access(_base(), "DB_URL", "read", "   ")

    def test_original_secrets_unchanged(self):
        base = _base()
        set_access(base, "DB_URL", "read", "alice")
        assert f"{ACCESS_META_PREFIX}DB_URL" not in base


class TestRemoveAccess:
    def test_removes_user_entry(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = remove_access(s, "DB_URL", "alice")
        acl = get_access(s, "DB_URL")
        assert "alice" not in acl

    def test_meta_key_deleted_when_no_users_remain(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = remove_access(s, "DB_URL", "alice")
        assert f"{ACCESS_META_PREFIX}DB_URL" not in s

    def test_missing_user_raises(self):
        with pytest.raises(AccessError, match="no access entry"):
            remove_access(_base(), "DB_URL", "ghost")


class TestCheckAccess:
    def test_exact_role_allowed(self):
        s = set_access(_base(), "DB_URL", "write", "alice")
        assert check_access(s, "DB_URL", "alice", "write") is True

    def test_higher_role_satisfies_lower(self):
        s = set_access(_base(), "DB_URL", "admin", "alice")
        assert check_access(s, "DB_URL", "alice", "read") is True

    def test_lower_role_denied_for_higher_requirement(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        assert check_access(s, "DB_URL", "alice", "write") is False

    def test_unknown_user_denied(self):
        assert check_access(_base(), "DB_URL", "nobody", "read") is False


class TestListUserKeys:
    def test_returns_keys_for_user(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = set_access(s, "API_KEY", "write", "alice")
        keys = list_user_keys(s, "alice")
        assert "DB_URL" in keys
        assert "API_KEY" in keys

    def test_excludes_keys_for_other_users(self):
        s = set_access(_base(), "DB_URL", "read", "bob")
        keys = list_user_keys(s, "alice")
        assert keys == []

    def test_returns_sorted_list(self):
        s = set_access(_base(), "DB_URL", "read", "alice")
        s = set_access(s, "API_KEY", "read", "alice")
        keys = list_user_keys(s, "alice")
        assert keys == sorted(keys)
