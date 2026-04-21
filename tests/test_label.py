"""Tests for envoy_cli.label."""

from __future__ import annotations

import json
import pytest

from envoy_cli.label import (
    LabelError,
    META_SUFFIX,
    _meta_key,
    add_label,
    get_labels,
    list_labeled,
    remove_label,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret"}


class TestAddLabel:
    def test_meta_key_added(self):
        result = add_label(_base(), "DB_URL", "database")
        assert _meta_key("DB_URL") in result

    def test_meta_key_value_contains_label(self):
        result = add_label(_base(), "DB_URL", "database")
        labels = json.loads(result[_meta_key("DB_URL")])
        assert "database" in labels

    def test_original_secrets_unchanged(self):
        base = _base()
        add_label(base, "DB_URL", "database")
        assert _meta_key("DB_URL") not in base

    def test_duplicate_label_not_added_twice(self):
        result = add_label(_base(), "DB_URL", "database")
        result2 = add_label(result, "DB_URL", "database")
        labels = json.loads(result2[_meta_key("DB_URL")])
        assert labels.count("database") == 1

    def test_multiple_labels_stored(self):
        result = add_label(_base(), "DB_URL", "database")
        result = add_label(result, "DB_URL", "production")
        labels = json.loads(result[_meta_key("DB_URL")])
        assert "database" in labels
        assert "production" in labels

    def test_labels_stored_sorted(self):
        result = add_label(_base(), "DB_URL", "zzz")
        result = add_label(result, "DB_URL", "aaa")
        labels = json.loads(result[_meta_key("DB_URL")])
        assert labels == sorted(labels)

    def test_missing_key_raises(self):
        with pytest.raises(LabelError, match="does not exist"):
            add_label(_base(), "MISSING", "x")

    def test_empty_label_raises(self):
        with pytest.raises(LabelError, match="non-empty"):
            add_label(_base(), "DB_URL", "")

    def test_whitespace_only_label_raises(self):
        with pytest.raises(LabelError, match="non-empty"):
            add_label(_base(), "DB_URL", "   ")

    def test_label_stripped_of_whitespace(self):
        result = add_label(_base(), "DB_URL", "  core  ")
        labels = json.loads(result[_meta_key("DB_URL")])
        assert "core" in labels


class TestRemoveLabel:
    def _seeded(self):
        base = _base()
        base = add_label(base, "DB_URL", "database")
        base = add_label(base, "DB_URL", "production")
        return base

    def test_label_removed(self):
        result = remove_label(self._seeded(), "DB_URL", "database")
        labels = get_labels(result, "DB_URL")
        assert "database" not in labels

    def test_other_labels_preserved(self):
        result = remove_label(self._seeded(), "DB_URL", "database")
        labels = get_labels(result, "DB_URL")
        assert "production" in labels

    def test_meta_key_removed_when_no_labels_left(self):
        seeded = add_label(_base(), "DB_URL", "only")
        result = remove_label(seeded, "DB_URL", "only")
        assert _meta_key("DB_URL") not in result

    def test_missing_key_raises(self):
        with pytest.raises(LabelError, match="does not exist"):
            remove_label(_base(), "MISSING", "x")

    def test_missing_label_raises(self):
        with pytest.raises(LabelError, match="not set"):
            remove_label(_base(), "DB_URL", "nonexistent")


class TestGetLabels:
    def test_returns_empty_list_when_none_set(self):
        assert get_labels(_base(), "DB_URL") == []

    def test_returns_correct_labels(self):
        seeded = add_label(_base(), "API_KEY", "auth")
        assert get_labels(seeded, "API_KEY") == ["auth"]

    def test_missing_key_raises(self):
        with pytest.raises(LabelError):
            get_labels(_base(), "NOPE")


class TestListLabeled:
    def test_returns_keys_with_label(self):
        base = _base()
        base = add_label(base, "DB_URL", "infra")
        base = add_label(base, "API_KEY", "infra")
        keys = list_labeled(base, "infra")
        assert "DB_URL" in keys
        assert "API_KEY" in keys

    def test_excludes_keys_without_label(self):
        base = add_label(_base(), "DB_URL", "infra")
        keys = list_labeled(base, "infra")
        assert "API_KEY" not in keys

    def test_returns_empty_when_no_matches(self):
        assert list_labeled(_base(), "ghost") == []

    def test_result_is_sorted(self):
        base = _base()
        base = add_label(base, "API_KEY", "shared")
        base = add_label(base, "DB_URL", "shared")
        keys = list_labeled(base, "shared")
        assert keys == sorted(keys)

    def test_meta_keys_excluded_from_results(self):
        base = add_label(_base(), "DB_URL", "infra")
        keys = list_labeled(base, "infra")
        for k in keys:
            assert not k.endswith(META_SUFFIX)
