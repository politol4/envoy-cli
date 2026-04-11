"""Tests for envoy_cli.clone."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from envoy_cli.clone import CloneError, clone_env
from envoy_cli.vault import Vault


def _make_vault(secrets: dict[str, str] | None = None) -> Vault:
    """Return an in-memory Vault pre-populated with *secrets*."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".vault") as fh:
        path = fh.name
    v = Vault(path)
    for k, val in (secrets or {}).items():
        v.set(k, val)
    return v


def _make_manager(src_vault: Vault, dst_vault: Vault) -> MagicMock:
    manager = MagicMock()
    manager._load_vault.side_effect = lambda env, pp: (
        src_vault if env == "staging" else dst_vault
    )
    manager._save_vault.return_value = None
    return manager


class TestCloneEnv(unittest.TestCase):
    def tearDown(self) -> None:
        # Clean up temp vault files created during tests
        for attr in ("_src", "_dst"):
            v = getattr(self, attr, None)
            if v and os.path.exists(v.path):
                os.unlink(v.path)

    # ------------------------------------------------------------------
    def test_same_env_raises(self) -> None:
        self._src = _make_vault({"A": "1"})
        self._dst = _make_vault()
        mgr = _make_manager(self._src, self._dst)
        with self.assertRaises(CloneError):
            clone_env(mgr, "staging", "staging", "pass")

    def test_empty_source_raises(self) -> None:
        self._src = _make_vault()
        self._dst = _make_vault()
        mgr = _make_manager(self._src, self._dst)
        with self.assertRaises(CloneError):
            clone_env(mgr, "staging", "production", "pass")

    def test_returns_count_of_written_secrets(self) -> None:
        self._src = _make_vault({"A": "1", "B": "2", "C": "3"})
        self._dst = _make_vault()
        mgr = _make_manager(self._src, self._dst)
        count = clone_env(mgr, "staging", "production", "pass")
        self.assertEqual(count, 3)

    def test_secrets_present_in_destination(self) -> None:
        self._src = _make_vault({"DB_URL": "postgres://", "SECRET": "abc"})
        self._dst = _make_vault()
        mgr = _make_manager(self._src, self._dst)
        clone_env(mgr, "staging", "production", "pass")
        self.assertEqual(self._dst.get("DB_URL"), "postgres://")
        self.assertEqual(self._dst.get("SECRET"), "abc")

    def test_existing_keys_preserved_when_no_overwrite(self) -> None:
        self._src = _make_vault({"KEY": "new_value"})
        self._dst = _make_vault({"KEY": "original"})
        mgr = _make_manager(self._src, self._dst)
        clone_env(mgr, "staging", "production", "pass", overwrite=False)
        self.assertEqual(self._dst.get("KEY"), "original")

    def test_existing_keys_overwritten_when_flag_set(self) -> None:
        self._src = _make_vault({"KEY": "new_value"})
        self._dst = _make_vault({"KEY": "original"})
        mgr = _make_manager(self._src, self._dst)
        clone_env(mgr, "staging", "production", "pass", overwrite=True)
        self.assertEqual(self._dst.get("KEY"), "new_value")

    def test_save_vault_called_once(self) -> None:
        self._src = _make_vault({"X": "1"})
        self._dst = _make_vault()
        mgr = _make_manager(self._src, self._dst)
        clone_env(mgr, "staging", "production", "pass")
        mgr._save_vault.assert_called_once_with("production", self._dst, "pass")

    def test_no_overwrite_skipped_keys_not_counted(self) -> None:
        self._src = _make_vault({"A": "1", "B": "2"})
        self._dst = _make_vault({"A": "existing"})
        mgr = _make_manager(self._src, self._dst)
        count = clone_env(mgr, "staging", "production", "pass", overwrite=False)
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
