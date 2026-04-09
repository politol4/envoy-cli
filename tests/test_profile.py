"""Tests for envoy_cli.profile."""

import json
import tempfile
from pathlib import Path

import pytest

from envoy_cli.profile import Profile, ProfileError, ProfileStore


class TestProfile:
    def test_to_dict_contains_required_fields(self):
        p = Profile("staging", "https://staging.example.com")
        d = p.to_dict()
        assert d["name"] == "staging"
        assert d["base_url"] == "https://staging.example.com"
        assert "vault_path" in d

    def test_trailing_slash_stripped_from_base_url(self):
        p = Profile("prod", "https://prod.example.com/")
        assert p.base_url == "https://prod.example.com"

    def test_from_dict_round_trip(self):
        original = Profile("dev", "http://localhost:8000", vault_path=".envoy/dev.vault")
        restored = Profile.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.base_url == original.base_url
        assert restored.vault_path == original.vault_path

    def test_empty_name_raises(self):
        with pytest.raises(ProfileError):
            Profile("", "https://example.com")

    def test_empty_base_url_raises(self):
        with pytest.raises(ProfileError):
            Profile("staging", "")

    def test_vault_path_defaults_to_none(self):
        p = Profile("staging", "https://staging.example.com")
        assert p.vault_path is None


class TestProfileStore:
    def _store(self, tmp_path: Path) -> ProfileStore:
        return ProfileStore(path=tmp_path / "profiles.json")

    def test_list_empty_when_no_file(self, tmp_path):
        store = self._store(tmp_path)
        assert store.list() == []

    def test_set_and_get(self, tmp_path):
        store = self._store(tmp_path)
        p = Profile("staging", "https://staging.example.com")
        store.set(p)
        retrieved = store.get("staging")
        assert retrieved.name == "staging"
        assert retrieved.base_url == "https://staging.example.com"

    def test_set_overwrites_existing(self, tmp_path):
        store = self._store(tmp_path)
        store.set(Profile("staging", "https://old.example.com"))
        store.set(Profile("staging", "https://new.example.com"))
        assert store.get("staging").base_url == "https://new.example.com"

    def test_list_returns_all_profiles(self, tmp_path):
        store = self._store(tmp_path)
        store.set(Profile("staging", "https://staging.example.com"))
        store.set(Profile("production", "https://prod.example.com"))
        names = {p.name for p in store.list()}
        assert names == {"staging", "production"}

    def test_delete_removes_profile(self, tmp_path):
        store = self._store(tmp_path)
        store.set(Profile("staging", "https://staging.example.com"))
        store.delete("staging")
        assert store.list() == []

    def test_get_missing_profile_raises(self, tmp_path):
        store = self._store(tmp_path)
        with pytest.raises(ProfileError, match="not found"):
            store.get("nonexistent")

    def test_delete_missing_profile_raises(self, tmp_path):
        store = self._store(tmp_path)
        with pytest.raises(ProfileError, match="not found"):
            store.delete("nonexistent")

    def test_creates_parent_directories(self, tmp_path):
        store = ProfileStore(path=tmp_path / "nested" / "dir" / "profiles.json")
        store.set(Profile("staging", "https://staging.example.com"))
        assert store.path.exists()

    def test_persisted_as_valid_json(self, tmp_path):
        store = self._store(tmp_path)
        store.set(Profile("staging", "https://staging.example.com"))
        with store.path.open() as fh:
            data = json.load(fh)
        assert "staging" in data
