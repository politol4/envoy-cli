"""Tests for envoy_cli.rotation."""

import tempfile
import unittest
from pathlib import Path

from envoy_cli.rotation import RotationError, rotate_key
from envoy_cli.vault import Vault


class TestRotateKey(unittest.TestCase):
    def _make_vault(self, path: Path, passphrase: str, entries: dict) -> None:
        """Helper: create and persist a vault with *entries*."""
        v = Vault(str(path), passphrase)
        for k, val in entries.items():
            v.set(k, val)
        v.save()

    # ------------------------------------------------------------------
    def test_same_passphrase_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "secret", {"KEY": "val"})
            with self.assertRaises(RotationError):
                rotate_key(vpath, "secret", "secret")

    def test_returns_count_of_rotated_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "old", {"A": "1", "B": "2", "C": "3"})
            count = rotate_key(vpath, "old", "new")
            self.assertEqual(count, 3)

    def test_rotated_vault_readable_with_new_passphrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "old", {"DB_URL": "postgres://localhost"})
            rotate_key(vpath, "old", "new")

            new_vault = Vault(str(vpath), "new")
            new_vault.load()
            self.assertEqual(new_vault.get("DB_URL"), "postgres://localhost")

    def test_rotated_vault_not_readable_with_old_passphrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "old", {"TOKEN": "abc123"})
            rotate_key(vpath, "old", "new")

            old_vault = Vault(str(vpath), "old")
            with self.assertRaises(Exception):
                old_vault.load()

    def test_empty_vault_rotates_zero_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "old", {})
            count = rotate_key(vpath, "old", "new")
            self.assertEqual(count, 0)

    def test_wrong_old_passphrase_raises_rotation_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            self._make_vault(vpath, "correct", {"X": "y"})
            with self.assertRaises(RotationError):
                rotate_key(vpath, "wrong", "new")

    def test_all_keys_preserved_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = Path(tmp) / "vault.json"
            entries = {"ALPHA": "a", "BETA": "b", "GAMMA": "c"}
            self._make_vault(vpath, "old", entries)
            rotate_key(vpath, "old", "new")

            new_vault = Vault(str(vpath), "new")
            new_vault.load()
            for key, value in entries.items():
                self.assertEqual(new_vault.get(key), value)


if __name__ == "__main__":
    unittest.main()
