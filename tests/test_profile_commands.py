"""Tests for envoy_cli.profile_commands."""

import pytest

from envoy_cli.profile import Profile, ProfileError, ProfileStore
from envoy_cli.profile_commands import (
    cmd_profile_add,
    cmd_profile_list,
    cmd_profile_remove,
    cmd_profile_show,
)


class TestCmdProfileAdd:
    def test_add_returns_added_message(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        msg = cmd_profile_add(store, "staging", "https://staging.example.com")
        assert "Added" in msg
        assert "staging" in msg

    def test_update_returns_updated_message(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        cmd_profile_add(store, "staging", "https://staging.example.com")
        msg = cmd_profile_add(store, "staging", "https://new.example.com")
        assert "Updated" in msg

    def test_profile_persisted_after_add(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        cmd_profile_add(store, "prod", "https://prod.example.com", vault_path=".envoy/prod.vault")
        p = store.get("prod")
        assert p.vault_path == ".envoy/prod.vault"

    def test_invalid_profile_raises(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        with pytest.raises(ProfileError):
            cmd_profile_add(store, "", "https://example.com")


class TestCmdProfileList:
    def test_empty_store_returns_hint(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        lines = cmd_profile_list(store)
        assert len(lines) == 1
        assert "profile add" in lines[0]

    def test_lists_all_profiles(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        store.set(Profile("staging", "https://staging.example.com"))
        store.set(Profile("production", "https://prod.example.com"))
        lines = cmd_profile_list(store)
        joined = "\n".join(lines)
        assert "staging" in joined
        assert "production" in joined

    def test_output_sorted_alphabetically(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        store.set(Profile("zzz", "https://zzz.example.com"))
        store.set(Profile("aaa", "https://aaa.example.com"))
        lines = cmd_profile_list(store)
        assert lines[0].strip().startswith("aaa")


class TestCmdProfileRemove:
    def test_remove_existing_profile(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        store.set(Profile("staging", "https://staging.example.com"))
        msg = cmd_profile_remove(store, "staging")
        assert "staging" in msg
        assert store.list() == []

    def test_remove_missing_profile_raises(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        with pytest.raises(ProfileError):
            cmd_profile_remove(store, "nonexistent")


class TestCmdProfileShow:
    def test_show_returns_detail_lines(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        store.set(Profile("staging", "https://staging.example.com", vault_path=".envoy/s.vault"))
        lines = cmd_profile_show(store, "staging")
        joined = "\n".join(lines)
        assert "staging" in joined
        assert "https://staging.example.com" in joined
        assert ".envoy/s.vault" in joined

    def test_show_missing_profile_raises(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        with pytest.raises(ProfileError):
            cmd_profile_show(store, "ghost")

    def test_show_default_vault_path_label(self, tmp_path):
        store = ProfileStore(path=tmp_path / "profiles.json")
        store.set(Profile("staging", "https://staging.example.com"))
        lines = cmd_profile_show(store, "staging")
        joined = "\n".join(lines)
        assert "(default)" in joined
