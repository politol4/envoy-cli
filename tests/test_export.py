"""Tests for envoy_cli.export."""

import json
import unittest

from envoy_cli.export import ExportError, export_secrets

_SECRETS = {
    "DB_PASSWORD": "s3cr3t",
    "API_KEY": "abc123",
    "GREETING": "hello world",
}


class TestExportSecrets(unittest.TestCase):
    # ------------------------------------------------------------------
    # dotenv format
    # ------------------------------------------------------------------
    def test_dotenv_format_key_equals_quoted_value(self):
        out = export_secrets({"FOO": "bar"}, fmt="dotenv")
        self.assertIn('FOO="bar"', out)

    def test_dotenv_format_sorted_keys(self):
        out = export_secrets(_SECRETS, fmt="dotenv")
        lines = [l for l in out.splitlines() if l]
        keys = [l.split("=")[0] for l in lines]
        self.assertEqual(keys, sorted(keys))

    def test_dotenv_format_ends_with_newline(self):
        out = export_secrets({"X": "1"}, fmt="dotenv")
        self.assertTrue(out.endswith("\n"))

    def test_dotenv_empty_secrets_returns_empty_string(self):
        out = export_secrets({}, fmt="dotenv")
        self.assertEqual(out, "")

    # ------------------------------------------------------------------
    # shell format
    # ------------------------------------------------------------------
    def test_shell_format_has_export_prefix(self):
        out = export_secrets({"FOO": "bar"}, fmt="shell")
        self.assertIn("export FOO=", out)

    def test_shell_format_quotes_values_with_spaces(self):
        out = export_secrets({"MSG": "hello world"}, fmt="shell")
        # shlex.quote wraps in single quotes when spaces present
        self.assertIn("'hello world'", out)

    def test_shell_format_ends_with_newline(self):
        out = export_secrets({"A": "1"}, fmt="shell")
        self.assertTrue(out.endswith("\n"))

    # ------------------------------------------------------------------
    # json format
    # ------------------------------------------------------------------
    def test_json_format_is_valid_json(self):
        out = export_secrets(_SECRETS, fmt="json")
        parsed = json.loads(out)
        self.assertIsInstance(parsed, dict)

    def test_json_format_preserves_all_keys(self):
        out = export_secrets(_SECRETS, fmt="json")
        parsed = json.loads(out)
        self.assertEqual(set(parsed.keys()), set(_SECRETS.keys()))

    def test_json_format_values_match(self):
        out = export_secrets({"K": "V"}, fmt="json")
        self.assertEqual(json.loads(out)["K"], "V")

    # ------------------------------------------------------------------
    # docker format
    # ------------------------------------------------------------------
    def test_docker_format_no_quotes(self):
        out = export_secrets({"FOO": "bar"}, fmt="docker")
        self.assertIn("FOO=bar", out)
        self.assertNotIn('"', out)

    def test_docker_format_ends_with_newline(self):
        out = export_secrets({"Z": "9"}, fmt="docker")
        self.assertTrue(out.endswith("\n"))

    # ------------------------------------------------------------------
    # error handling
    # ------------------------------------------------------------------
    def test_unsupported_format_raises_export_error(self):
        with self.assertRaises(ExportError):
            export_secrets({"X": "1"}, fmt="xml")  # type: ignore[arg-type]

    def test_export_error_message_contains_format_name(self):
        with self.assertRaises(ExportError) as ctx:
            export_secrets({}, fmt="yaml")  # type: ignore[arg-type]
        self.assertIn("yaml", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
