"""Tests for envoy_cli.pin module."""

import pytest

from envoy_cli.pin import (
    PinError,
    _meta_key,
    filter_unpinned,
    is_pinned,
    list_pinned,
    pin_key,
    unpin_key,
)


def _base() -> dict:
    return {"DB_URL": "postgres://localhost", "SECRET": "abc123"}


class TestPinKey:
    def test_adds_meta_key(self):
        result = pin_key(_base(), "DB_URL")
        assert result[_meta_key("DB_URL")] == "pinned"

    def test_original_value_preserved(self):
        result = pin_key(_base(), "DB_URL")
        assert result["DB_URL"] == "postgres://localhost"

    def test_missing_key_raises(self):
        with pytest.raises(PinError, match="does not exist"):
            pin_key(_base(), "MISSING")

    def test_already_pinned_raises(self):
        once = pin_key(_base(), "DB_URL")
        with pytest.raises(PinError, match="already pinned"):
            pin_key(once, "DB_URL")

    def test_does_not_mutate_original(self):
        original = _base()
        pin_key(original, "DB_URL")
        assert _meta_key("DB_URL") not in original


class TestUnpinKey:
    def test_removes_meta_key(self):
        pinned = pin_key(_base(), "DB_URL")
        result = unpin_key(pinned, "DB_URL")
        assert _meta_key("DB_URL") not in result

    def test_not_pinned_raises(self):
        with pytest.raises(PinError, match="not pinned"):
            unpin_key(_base(), "DB_URL")

    def test_does_not_mutate_original(self):
        pinned = pin_key(_base(), "DB_URL")
        unpin_key(pinned, "DB_URL")
        assert _meta_key("DB_URL") in pinned


class TestIsPinned:
    def test_true_when_pinned(self):
        pinned = pin_key(_base(), "SECRET")
        assert is_pinned(pinned, "SECRET") is True

    def test_false_when_not_pinned(self):
        assert is_pinned(_base(), "SECRET") is False


class TestListPinned:
    def test_returns_pinned_keys(self):
        secrets = pin_key(pin_key(_base(), "DB_URL"), "SECRET")
        assert list_pinned(secrets) == ["DB_URL", "SECRET"]

    def test_excludes_meta_keys(self):
        secrets = pin_key(_base(), "DB_URL")
        pinned = list_pinned(secrets)
        assert all(not k.startswith("__pin__") for k in pinned)

    def test_empty_when_none_pinned(self):
        assert list_pinned(_base()) == []


class TestFilterUnpinned:
    def test_pinned_key_excluded_from_incoming(self):
        current = pin_key(_base(), "DB_URL")
        incoming = {"DB_URL": "new_value", "SECRET": "new_secret"}
        result = filter_unpinned(incoming, current)
        assert "DB_URL" not in result
        assert result["SECRET"] == "new_secret"

    def test_all_pass_when_none_pinned(self):
        incoming = {"DB_URL": "new", "SECRET": "new"}
        result = filter_unpinned(incoming, _base())
        assert result == incoming
