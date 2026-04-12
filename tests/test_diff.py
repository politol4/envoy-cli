"""Tests for envoy_cli.diff module."""

import unittest
from envoy_cli.diff import compute_diff, DiffResult


class TestComputeDiff(unittest.TestCase):

    def _local(self):
        return {"KEY_A": "alpha", "KEY_B": "beta", "KEY_C": "gamma"}

    def _remote(self):
        return {"KEY_B": "beta", "KEY_C": "CHANGED", "KEY_D": "delta"}

    def test_returns_diff_result(self):
        result = compute_diff(self._local(), self._remote())
        self.assertIsInstance(result, DiffResult)

    def test_added_keys(self):
        result = compute_diff(self._local(), self._remote())
        self.assertIn("KEY_A", result.added)
        self.assertEqual(result.added["KEY_A"], "alpha")

    def test_removed_keys(self):
        result = compute_diff(self._local(), self._remote())
        self.assertIn("KEY_D", result.removed)
        self.assertEqual(result.removed["KEY_D"], "delta")

    def test_changed_keys(self):
        result = compute_diff(self._local(), self._remote())
        self.assertIn("KEY_C", result.changed)
        old, new = result.changed["KEY_C"]
        self.assertEqual(old, "gamma")
        self.assertEqual(new, "CHANGED")

    def test_unchanged_keys(self):
        result = compute_diff(self._local(), self._remote())
        self.assertIn("KEY_B", result.unchanged)

    def test_no_changes(self):
        env = {"A": "1", "B": "2"}
        result = compute_diff(env, env.copy())
        self.assertFalse(result.has_changes)

    def test_has_changes_true(self):
        result = compute_diff(self._local(), self._remote())
        self.assertTrue(result.has_changes)

    def test_empty_local(self):
        result = compute_diff({}, {"X": "1"})
        self.assertIn("X", result.removed)
        self.assertFalse(result.added)

    def test_empty_remote(self):
        result = compute_diff({"X": "1"}, {})
        self.assertIn("X", result.added)
        self.assertFalse(result.removed)


class TestDiffResultSummary(unittest.TestCase):

    def test_summary_no_changes(self):
        r = DiffResult()
        self.assertEqual(r.summary(), "No changes.")

    def test_summary_with_changes(self):
        r = DiffResult(added={"A": "1"}, removed={"B": "2"}, changed={"C": ("x", "y")})
        summary = r.summary()
        self.assertIn("+1 added", summary)
        self.assertIn("-1 removed", summary)
        self.assertIn("~1 changed", summary)

    def test_as_lines_masked(self):
        r = DiffResult(added={"SECRET": "s3cr3t"})
        lines = r.as_lines(mask_values=True)
        self.assertEqual(len(lines), 1)
        self.assertIn("SECRET", lines[0])
        self.assertNotIn("s3cr3t", lines[0])

    def test_as_lines_unmasked(self):
        r = DiffResult(added={"KEY": "val"})
        lines = r.as_lines(mask_values=False)
        self.assertIn("val", lines[0])

    def test_as_lines_changed_format(self):
        r = DiffResult(changed={"KEY": ("old", "new")})
        lines = r.as_lines(mask_values=False)
        self.assertTrue(lines[0].startswith("~"))
        self.assertIn("KEY", lines[0])
        self.assertIn("old", lines[0])
        self.assertIn("new", lines[0])
