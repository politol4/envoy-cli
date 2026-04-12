"""Tests for envoy_cli.archive."""

import pytest

from envoy_cli.archive import (
    ARCHIVE_PREFIX,
    ArchiveError,
    archive_key,
    list_archived,
    purge_archived,
    unarchive_key,
)


def _base() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "s3cr3t"}


class TestArchiveKey:
    def test_key_moved_to_archive_namespace(self):
        result = archive_key(_base(), "DB_HOST")
        assert f"{ARCHIVE_PREFIX}DB_HOST" in result

    def test_original_key_removed(self):
        result = archive_key(_base(), "DB_HOST")
        assert "DB_HOST" not in result

    def test_value_preserved(self):
        result = archive_key(_base(), "DB_HOST")
        assert result[f"{ARCHIVE_PREFIX}DB_HOST"] == "localhost"

    def test_missing_key_raises(self):
        with pytest.raises(ArchiveError, match="not found"):
            archive_key(_base(), "MISSING")

    def test_empty_key_raises(self):
        with pytest.raises(ArchiveError, match="empty"):
            archive_key(_base(), "")

    def test_already_archived_raises(self):
        archived = archive_key(_base(), "DB_HOST")
        with pytest.raises(ArchiveError, match="already archived"):
            archive_key(archived, f"{ARCHIVE_PREFIX}DB_HOST")

    def test_other_keys_unchanged(self):
        result = archive_key(_base(), "DB_HOST")
        assert result["DB_PORT"] == "5432"
        assert result["SECRET"] == "s3cr3t"


class TestUnarchiveKey:
    def _archived(self) -> dict:
        return archive_key(_base(), "DB_HOST")

    def test_key_restored_to_live(self):
        result = unarchive_key(self._archived(), "DB_HOST")
        assert "DB_HOST" in result

    def test_archive_entry_removed(self):
        result = unarchive_key(self._archived(), "DB_HOST")
        assert f"{ARCHIVE_PREFIX}DB_HOST" not in result

    def test_value_preserved_after_restore(self):
        result = unarchive_key(self._archived(), "DB_HOST")
        assert result["DB_HOST"] == "localhost"

    def test_not_archived_raises(self):
        with pytest.raises(ArchiveError, match="not archived"):
            unarchive_key(_base(), "DB_HOST")

    def test_empty_key_raises(self):
        with pytest.raises(ArchiveError, match="empty"):
            unarchive_key(self._archived(), "")

    def test_conflict_with_live_key_raises(self):
        secrets = dict(_base())
        secrets[f"{ARCHIVE_PREFIX}DB_HOST"] = "old_value"
        with pytest.raises(ArchiveError, match="already exists"):
            unarchive_key(secrets, "DB_HOST")


class TestListArchived:
    def test_returns_empty_when_none_archived(self):
        assert list_archived(_base()) == []

    def test_returns_original_key_names(self):
        secrets = archive_key(_base(), "DB_HOST")
        secrets = archive_key(secrets, "SECRET")
        names = list_archived(secrets)
        assert "DB_HOST" in names
        assert "SECRET" in names

    def test_results_are_sorted(self):
        secrets = archive_key(_base(), "SECRET")
        secrets = archive_key(secrets, "DB_HOST")
        assert list_archived(secrets) == sorted(list_archived(secrets))


class TestPurgeArchived:
    def test_removes_archived_keys(self):
        secrets = archive_key(_base(), "DB_HOST")
        result = purge_archived(secrets)
        assert f"{ARCHIVE_PREFIX}DB_HOST" not in result

    def test_preserves_live_keys(self):
        secrets = archive_key(_base(), "DB_HOST")
        result = purge_archived(secrets)
        assert "DB_PORT" in result
        assert "SECRET" in result

    def test_no_archived_keys_unchanged(self):
        result = purge_archived(_base())
        assert result == _base()
