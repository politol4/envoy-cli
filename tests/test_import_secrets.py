"""Tests for envoy_cli.import_secrets."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from envoy_cli.import_secrets import ImportError as ImportErr
from envoy_cli.import_secrets import import_from_file, import_secrets


class TestImportSecretsDotenv(unittest.TestCase):
    def test_basic_dotenv(self):
        result = import_secrets("FOO=bar\nBAZ=qux\n")
        self.assertEqual(result, {"FOO": "bar", "BAZ": "qux"})

    def test_empty_source_raises(self):
        with self.assertRaises(ImportErr):
            import_secrets("")

    def test_prefix_filter_keeps_matching_keys(self):
        src = "APP_HOST=localhost\nAPP_PORT=5432\nOTHER=x\n"
        result = import_secrets(src, prefix_filter="APP_")
        self.assertIn("APP_HOST", result)
        self.assertIn("APP_PORT", result)
        self.assertNotIn("OTHER", result)

    def test_prefix_filter_no_match_raises(self):
        with self.assertRaises(ImportErr):
            import_secrets("FOO=bar\n", prefix_filter="MISSING_")

    def test_overwrite_true_replaces_existing(self):
        existing = {"FOO": "old"}
        result = import_secrets("FOO=new\n", existing=existing, overwrite=True)
        self.assertEqual(result["FOO"], "new")

    def test_overwrite_false_preserves_existing(self):
        existing = {"FOO": "old"}
        result = import_secrets("FOO=new\n", existing=existing, overwrite=False)
        self.assertEqual(result["FOO"], "old")

    def test_merge_adds_new_keys(self):
        existing = {"EXISTING": "yes"}
        result = import_secrets("NEW=key\n", existing=existing)
        self.assertIn("EXISTING", result)
        self.assertIn("NEW", result)


class TestImportSecretsJSON(unittest.TestCase):
    def test_basic_json(self):
        src = json.dumps({"DB_HOST": "db.local", "DB_PORT": "5432"})
        result = import_secrets(src, fmt="json")
        self.assertEqual(result["DB_HOST"], "db.local")
        self.assertEqual(result["DB_PORT"], "5432")

    def test_non_string_values_coerced(self):
        src = json.dumps({"PORT": 8080, "DEBUG": True})
        result = import_secrets(src, fmt="json")
        self.assertEqual(result["PORT"], "8080")
        self.assertEqual(result["DEBUG"], "True")

    def test_invalid_json_raises(self):
        with self.assertRaises(ImportErr):
            import_secrets("{not valid json}", fmt="json")

    def test_json_array_raises(self):
        with self.assertRaises(ImportErr):
            import_secrets("[1, 2, 3]", fmt="json")


class TestImportSecretsUnsupportedFormat(unittest.TestCase):
    def test_unsupported_format_raises(self):
        with self.assertRaises(ImportErr):
            import_secrets("FOO=bar", fmt="yaml")


class TestImportFromFile(unittest.TestCase):
    def _write_tmp(self, content: str, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "w") as fh:
            fh.write(content)
        return path

    def test_dotenv_file_auto_detected(self):
        path = self._write_tmp("KEY=val\n", ".env")
        result = import_from_file(path)
        self.assertEqual(result["KEY"], "val")
        os.unlink(path)

    def test_json_file_auto_detected(self):
        path = self._write_tmp(json.dumps({"K": "v"}), ".json")
        result = import_from_file(path)
        self.assertEqual(result["K"], "v")
        os.unlink(path)

    def test_missing_file_raises(self):
        with self.assertRaises(ImportErr):
            import_from_file("/nonexistent/path/.env")


if __name__ == "__main__":
    unittest.main()
