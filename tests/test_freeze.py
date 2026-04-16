import pytest
from envoy_cli.freeze import (
    freeze_key,
    unfreeze_key,
    is_frozen,
    list_frozen,
    guard_frozen,
    FreezeError,
)


def _base():
    return {"DB_URL": "postgres://localhost", "SECRET_KEY": "abc123"}


class TestFreezeKey:
    def test_meta_key_added(self):
        result = freeze_key(_base(), "DB_URL")
        assert "__freeze__.DB_URL" in result

    def test_original_value_preserved(self):
        result = freeze_key(_base(), "DB_URL")
        assert result["DB_URL"] == "postgres://localhost"

    def test_missing_key_raises(self):
        with pytest.raises(FreezeError, match="not found"):
            freeze_key(_base(), "MISSING")

    def test_does_not_mutate_input(self):
        secrets = _base()
        freeze_key(secrets, "DB_URL")
        assert "__freeze__.DB_URL" not in secrets


class TestUnfreezeKey:
    def test_meta_key_removed(self):
        frozen = freeze_key(_base(), "DB_URL")
        result = unfreeze_key(frozen, "DB_URL")
        assert "__freeze__.DB_URL" not in result

    def test_original_value_still_present(self):
        frozen = freeze_key(_base(), "DB_URL")
        result = unfreeze_key(frozen, "DB_URL")
        assert result["DB_URL"] == "postgres://localhost"

    def test_unfreeze_not_frozen_raises(self):
        with pytest.raises(FreezeError, match="not frozen"):
            unfreeze_key(_base(), "DB_URL")


class TestIsFrozen:
    def test_true_when_frozen(self):
        frozen = freeze_key(_base(), "SECRET_KEY")
        assert is_frozen(frozen, "SECRET_KEY") is True

    def test_false_when_not_frozen(self):
        assert is_frozen(_base(), "SECRET_KEY") is False


class TestListFrozen:
    def test_returns_frozen_keys(self):
        s = freeze_key(freeze_key(_base(), "DB_URL"), "SECRET_KEY")
        assert list_frozen(s) == ["DB_URL", "SECRET_KEY"]

    def test_empty_when_none_frozen(self):
        assert list_frozen(_base()) == []

    def test_sorted_order(self):
        s = freeze_key(freeze_key(_base(), "SECRET_KEY"), "DB_URL")
        assert list_frozen(s) == ["DB_URL", "SECRET_KEY"]


class TestGuardFrozen:
    def test_raises_when_frozen(self):
        frozen = freeze_key(_base(), "DB_URL")
        with pytest.raises(FreezeError, match="frozen"):
            guard_frozen(frozen, "DB_URL")

    def test_passes_when_not_frozen(self):
        guard_frozen(_base(), "DB_URL")  # should not raise
