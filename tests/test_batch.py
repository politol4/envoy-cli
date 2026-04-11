"""Tests for envoy_cli.batch and envoy_cli.batch_commands."""

from __future__ import annotations

import os
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import MagicMock, patch

from envoy_cli.batch import BatchError, batch_delete, batch_set
from envoy_cli.batch_commands import cmd_batch_delete, cmd_batch_set
from envoy_cli.vault import Vault

PASS = "hunter2"


def _make_vault(tmp_dir: str, env: str = "test") -> Vault:
    path = os.path.join(tmp_dir, f"{env}.vault")
    v = Vault(path, PASS)
    v.save()
    return v


def _make_manager(tmp_dir: str):
    mgr = MagicMock()

    def _load_vault(env, passphrase):
        path = os.path.join(tmp_dir, f"{env}.vault")
        return Vault(path, passphrase)

    mgr._load_vault.side_effect = _load_vault
    mgr.base_dir = tmp_dir
    return mgr


class TestBatchSet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _make_vault(self.tmp)
        self.manager = _make_manager(self.tmp)

    def test_empty_pairs_raises(self):
        with self.assertRaises(BatchError):
            batch_set(self.manager, "test", PASS, {})

    def test_empty_key_raises(self):
        with self.assertRaises(BatchError):
            batch_set(self.manager, "test", PASS, {"": "val"})

    def test_sets_multiple_keys(self):
        applied, skipped = batch_set(
            self.manager, "test", PASS, {"A": "1", "B": "2"}
        )
        self.assertEqual(sorted(applied), ["A", "B"])
        self.assertEqual(skipped, [])

    def test_skip_existing_when_no_overwrite(self):
        batch_set(self.manager, "test", PASS, {"A": "old"})
        applied, skipped = batch_set(
            self.manager, "test", PASS, {"A": "new", "B": "2"},
            overwrite=False,
        )
        self.assertIn("B", applied)
        self.assertIn("A", skipped)

    def test_values_persisted(self):
        batch_set(self.manager, "test", PASS, {"X": "hello"})
        vault = Vault(os.path.join(self.tmp, "test.vault"), PASS)
        self.assertEqual(vault.get("X"), "hello")


class TestBatchDelete(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        v = _make_vault(self.tmp)
        v.set("K1", "v1")
        v.set("K2", "v2")
        v.save()
        self.manager = _make_manager(self.tmp)

    def test_empty_keys_raises(self):
        with self.assertRaises(BatchError):
            batch_delete(self.manager, "test", PASS, [])

    def test_missing_key_raises_by_default(self):
        with self.assertRaises(BatchError):
            batch_delete(self.manager, "test", PASS, ["NOPE"])

    def test_missing_key_skipped_when_ignore_missing(self):
        deleted, missing = batch_delete(
            self.manager, "test", PASS, ["NOPE"], ignore_missing=True
        )
        self.assertEqual(deleted, [])
        self.assertIn("NOPE", missing)

    def test_deletes_multiple_keys(self):
        deleted, missing = batch_delete(self.manager, "test", PASS, ["K1", "K2"])
        self.assertEqual(sorted(deleted), ["K1", "K2"])
        vault = Vault(os.path.join(self.tmp, "test.vault"), PASS)
        self.assertIsNone(vault.get("K1"))
        self.assertIsNone(vault.get("K2"))


class TestCmdBatchSet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        _make_vault(self.tmp)

    def _args(self, pairs, no_overwrite=False):
        return Namespace(
            pairs=pairs, env="test", passphrase=PASS,
            vault_dir=self.tmp, no_overwrite=no_overwrite,
        )

    def test_returns_set_message(self):
        result = cmd_batch_set(self._args(["FOO=bar", "BAZ=qux"]))
        self.assertIn("Set 2", result)

    def test_invalid_pair_raises(self):
        with self.assertRaises(BatchError):
            cmd_batch_set(self._args(["NOEQUALSSIGN"]))


class TestCmdBatchDelete(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        v = _make_vault(self.tmp)
        v.set("DEL1", "x")
        v.save()

    def _args(self, keys, ignore_missing=False):
        return Namespace(
            keys=keys, env="test", passphrase=PASS,
            vault_dir=self.tmp, ignore_missing=ignore_missing,
        )

    def test_returns_deleted_message(self):
        result = cmd_batch_delete(self._args(["DEL1"]))
        self.assertIn("Deleted 1", result)

    def test_missing_key_with_flag_returns_skipped_message(self):
        result = cmd_batch_delete(self._args(["GHOST"], ignore_missing=True))
        self.assertIn("Missing", result)
