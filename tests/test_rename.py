"""Tests for envoy_cli.rename."""

import unittest
from unittest.mock import MagicMock

from envoy_cli.rename import RenameError, rename_key


def _make_vault(secrets: dict) -> MagicMock:
    """Build a minimal Vault mock backed by *secrets* (mutated in place)."""
    vault = MagicMock()
    vault.all.side_effect = lambda: dict(secrets)
    vault.get.side_effect = lambda k: secrets[k]  # raises KeyError if missing
    vault.set.side_effect = lambda k, v: secrets.update({k: v})
    vault.delete.side_effect = lambda k: secrets.pop(k, None)
    return vault


class TestRenameKey(unittest.TestCase):

    def test_value_moved_to_new_key(self):
        secrets = {"OLD": "my_value"}
        vault = _make_vault(secrets)
        rename_key(vault, "OLD", "NEW")
        self.assertEqual(secrets.get("NEW"), "my_value")

    def test_old_key_removed(self):
        secrets = {"OLD": "my_value"}
        vault = _make_vault(secrets)
        rename_key(vault, "OLD", "NEW")
        self.assertNotIn("OLD", secrets)

    def test_missing_old_key_raises(self):
        secrets = {"OTHER": "val"}
        vault = _make_vault(secrets)
        with self.assertRaises(RenameError) as ctx:
            rename_key(vault, "MISSING", "NEW")
        self.assertIn("MISSING", str(ctx.exception))

    def test_existing_new_key_raises(self):
        secrets = {"OLD": "v1", "NEW": "v2"}
        vault = _make_vault(secrets)
        with self.assertRaises(RenameError) as ctx:
            rename_key(vault, "OLD", "NEW")
        self.assertIn("NEW", str(ctx.exception))

    def test_empty_old_key_raises(self):
        vault = _make_vault({})
        with self.assertRaises(RenameError):
            rename_key(vault, "", "NEW")

    def test_empty_new_key_raises(self):
        vault = _make_vault({"OLD": "v"})
        with self.assertRaises(RenameError):
            rename_key(vault, "OLD", "  ")

    def test_tag_metadata_migrated(self):
        secrets = {"OLD": "val", "__tags__.OLD": "important,secret"}
        vault = _make_vault(secrets)
        rename_key(vault, "OLD", "NEW")
        self.assertIn("__tags__.NEW", secrets)
        self.assertEqual(secrets["__tags__.NEW"], "important,secret")
        self.assertNotIn("__tags__.OLD", secrets)

    def test_rename_without_tags_does_not_raise(self):
        secrets = {"OLD": "val"}
        vault = _make_vault(secrets)
        # Should complete without error even if no tag metadata exists.
        rename_key(vault, "OLD", "NEW")
        self.assertIn("NEW", secrets)

    def test_whitespace_stripped_from_keys(self):
        secrets = {"OLD": "val"}
        vault = _make_vault(secrets)
        rename_key(vault, "  OLD  ", "  NEW  ")
        self.assertIn("NEW", secrets)
        self.assertNotIn("OLD", secrets)


if __name__ == "__main__":
    unittest.main()
