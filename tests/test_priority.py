"""Tests for envoy_cli.priority."""

from __future__ import annotations

import pytest

from envoy_cli.priority import (
    PriorityError,
    _meta_key,
    set_priority,
    remove_priority,
    get_priority,
    list_by_priority,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret", "TIMEOUT": "30"}


class TestSetPriority:
    def test_meta_key_added(self):
        result = set_priority(_base(), "DB_URL", "high")
        assert _meta_key("DB_URL") in result

    def test_meta_key_value_is_level(self):
        result = set_priority(_base(), "DB_URL", "critical")
        assert result[_meta_key("DB_URL")] == "critical"

    def test_original_secrets_unchanged(self):
        base = _base()
        result = set_priority(base, "DB_URL", "low")
        assert result["DB_URL"] == base["DB_URL"]

    def test_case_insensitive_level(self):
        result = set_priority(_base(), "API_KEY", "HIGH")
        assert result[_meta_key("API_KEY")] == "high"

    def test_missing_key_raises(self):
        with pytest.raises(PriorityError, match="not found"):
            set_priority(_base(), "MISSING", "low")

    def test_invalid_level_raises(self):
        with pytest.raises(PriorityError, match="Invalid priority"):
            set_priority(_base(), "DB_URL", "urgent")

    def test_does_not_mutate_input(self):
        base = _base()
        set_priority(base, "DB_URL", "normal")
        assert _meta_key("DB_URL") not in base


class TestRemovePriority:
    def test_meta_key_removed(self):
        secrets = set_priority(_base(), "DB_URL", "high")
        result = remove_priority(secrets, "DB_URL")
        assert _meta_key("DB_URL") not in result

    def test_original_value_preserved(self):
        secrets = set_priority(_base(), "DB_URL", "high")
        result = remove_priority(secrets, "DB_URL")
        assert result["DB_URL"] == secrets["DB_URL"]

    def test_remove_when_no_priority_set_is_noop(self):
        base = _base()
        result = remove_priority(base, "DB_URL")
        assert result == base

    def test_missing_key_raises(self):
        with pytest.raises(PriorityError, match="not found"):
            remove_priority(_base(), "GHOST")


class TestGetPriority:
    def test_returns_level_when_set(self):
        secrets = set_priority(_base(), "API_KEY", "critical")
        assert get_priority(secrets, "API_KEY") == "critical"

    def test_returns_none_when_not_set(self):
        assert get_priority(_base(), "DB_URL") is None

    def test_missing_key_raises(self):
        with pytest.raises(PriorityError, match="not found"):
            get_priority(_base(), "NOPE")


class TestListByPriority:
    def test_returns_all_real_keys(self):
        items = list_by_priority(_base())
        keys = [k for k, _ in items]
        assert set(keys) == {"DB_URL", "API_KEY", "TIMEOUT"}

    def test_excludes_meta_keys(self):
        secrets = set_priority(_base(), "DB_URL", "high")
        items = list_by_priority(secrets)
        keys = [k for k, _ in items]
        assert not any(k.startswith("__priority__") for k in keys)

    def test_critical_comes_first(self):
        secrets = _base()
        secrets = set_priority(secrets, "TIMEOUT", "critical")
        secrets = set_priority(secrets, "DB_URL", "low")
        items = list_by_priority(secrets)
        assert items[0][0] == "TIMEOUT"

    def test_unset_priority_level_label(self):
        items = list_by_priority(_base())
        levels = [lvl for _, lvl in items]
        assert all(lvl == "unset" for lvl in levels)

    def test_empty_secrets_returns_empty(self):
        assert list_by_priority({}) == []
