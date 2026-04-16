"""Tests for envoy_cli.env_switch."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from envoy_cli.env_switch import get_active, set_active, clear_active, SwitchError


def _profiles(*names):
    return {n: MagicMock() for n in names}


class TestGetActive:
    def test_returns_none_when_no_state_file(self, tmp_path):
        assert get_active(str(tmp_path)) is None

    def test_returns_name_after_set(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("staging")
        assert get_active(str(tmp_path)) == "staging"

    def test_returns_none_for_empty_state_file(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("  ")
        assert get_active(str(tmp_path)) is None


class TestSetActive:
    def test_creates_state_file(self, tmp_path):
        set_active("production", _profiles("production"), str(tmp_path))
        assert (tmp_path / ".envoy_active").read_text() == "production"

    def test_returns_confirmation_message(self, tmp_path):
        msg = set_active("staging", _profiles("staging"), str(tmp_path))
        assert "staging" in msg

    def test_unknown_profile_raises(self, tmp_path):
        with pytest.raises(SwitchError, match="Unknown environment"):
            set_active("ghost", _profiles("dev", "staging"), str(tmp_path))

    def test_empty_name_raises(self, tmp_path):
        with pytest.raises(SwitchError, match="must not be empty"):
            set_active("", _profiles("dev"), str(tmp_path))

    def test_overwrites_existing_state(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("dev")
        set_active("staging", _profiles("dev", "staging"), str(tmp_path))
        assert (tmp_path / ".envoy_active").read_text() == "staging"

    def test_error_message_lists_known_profiles(self, tmp_path):
        with pytest.raises(SwitchError, match="dev"):
            set_active("ghost", _profiles("dev"), str(tmp_path))


class TestClearActive:
    def test_removes_state_file(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("dev")
        clear_active(str(tmp_path))
        assert not (tmp_path / ".envoy_active").exists()

    def test_returns_cleared_message(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("dev")
        msg = clear_active(str(tmp_path))
        assert "cleared" in msg.lower()

    def test_no_file_returns_not_set_message(self, tmp_path):
        msg = clear_active(str(tmp_path))
        assert "No active" in msg

    def test_get_returns_none_after_clear(self, tmp_path):
        (tmp_path / ".envoy_active").write_text("dev")
        clear_active(str(tmp_path))
        assert get_active(str(tmp_path)) is None
