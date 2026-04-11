"""Tests for envoy_cli/copy.py."""

import unittest

from envoy_cli.copy import CopyError, copy_key
from envoy_cli.vault import Vault


def _make_vault(secrets=None):
    v = Vault.__new__(Vault)
    v._secrets = dict(secrets or {})
    # Minimal method stubs
    v.all = lambda: dict(v._secrets)
    v.set = lambda k, val: v._secrets.update({k: val})
    v.delete = lambda k: v._secrets.pop(k, None)
    return v


class TestCopyKey(unittest.TestCase):

    def test_value_present_at_dst(self):
        vault = _make_vault({"API_KEY": "secret123"})
        copy_key(vault, "API_KEY", "API_KEY_BACKUP")
        self.assertEqual(vault._secrets["API_KEY_BACKUP"], "secret123")

    def test_src_still_present_after_copy(self):
        vault = _make_vault({"API_KEY": "secret123"})
        copy_key(vault, "API_KEY", "API_KEY_BACKUP")
        self.assertIn("API_KEY", vault._secrets)

    def test_move_removes_src(self):
        vault = _make_vault({"OLD_KEY": "value"})
        copy_key(vault, "OLD_KEY", "NEW_KEY", move=True)
        self.assertNotIn("OLD_KEY", vault._secrets)

    def test_move_sets_dst(self):
        vault = _make_vault({"OLD_KEY": "value"})
        copy_key(vault, "OLD_KEY", "NEW_KEY", move=True)
        self.assertEqual(vault._secrets["NEW_KEY"], "value")

    def test_action_copy_returned(self):
        vault = _make_vault({"K": "v"})
        result = copy_key(vault, "K", "K2")
        self.assertEqual(result["action"], "copied")

    def test_action_moved_returned(self):
        vault = _make_vault({"K": "v"})
        result = copy_key(vault, "K", "K2", move=True)
        self.assertEqual(result["action"], "moved")

    def test_missing_src_raises(self):
        vault = _make_vault({})
        with self.assertRaises(CopyError):
            copy_key(vault, "MISSING", "DST")

    def test_empty_src_key_raises(self):
        vault = _make_vault({"K": "v"})
        with self.assertRaises(CopyError):
            copy_key(vault, "", "DST")

    def test_empty_dst_key_raises(self):
        vault = _make_vault({"K": "v"})
        with self.assertRaises(CopyError):
            copy_key(vault, "K", "")

    def test_same_src_dst_raises(self):
        vault = _make_vault({"K": "v"})
        with self.assertRaises(CopyError):
            copy_key(vault, "K", "K")

    def test_no_overwrite_raises_when_dst_exists(self):
        vault = _make_vault({"A": "1", "B": "2"})
        with self.assertRaises(CopyError):
            copy_key(vault, "A", "B", overwrite=False)

    def test_overwrite_replaces_dst(self):
        vault = _make_vault({"A": "new", "B": "old"})
        copy_key(vault, "A", "B", overwrite=True)
        self.assertEqual(vault._secrets["B"], "new")

    def test_result_contains_src_and_dst(self):
        vault = _make_vault({"X": "val"})
        result = copy_key(vault, "X", "Y")
        self.assertEqual(result["src"], "X")
        self.assertEqual(result["dst"], "Y")


if __name__ == "__main__":
    unittest.main()
