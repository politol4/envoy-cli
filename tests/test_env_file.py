"""Tests for envoy_cli.env_file — .env parsing and serialization."""

import textwrap
from pathlib import Path

import pytest

from envoy_cli.env_file import load_file, parse, save_file, serialize


class TestParse:
    def test_simple_key_value(self):
        assert parse("KEY=value") == {"KEY": "value"}

    def test_double_quoted_value(self):
        assert parse('DB_URL="postgres://localhost/db"') == {
            "DB_URL": "postgres://localhost/db"
        }

    def test_single_quoted_value(self):
        assert parse("SECRET='my secret'") == {"SECRET": "my secret"}

    def test_export_prefix_stripped(self):
        assert parse("export API_KEY=abc123") == {"API_KEY": "abc123"}

    def test_inline_comment_stripped(self):
        assert parse("PORT=8080 # default port") == {"PORT": "8080"}

    def test_blank_lines_ignored(self):
        text = "\n\nKEY=val\n\n"
        assert parse(text) == {"KEY": "val"}

    def test_comment_lines_ignored(self):
        text = "# This is a comment\nKEY=val"
        assert parse(text) == {"KEY": "val"}

    def test_multiple_keys(self):
        text = textwrap.dedent("""\
            APP_ENV=production
            DEBUG=false
            PORT=443
        """)
        assert parse(text) == {
            "APP_ENV": "production",
            "DEBUG": "false",
            "PORT": "443",
        }

    def test_empty_value(self):
        assert parse("EMPTY=") == {"EMPTY": ""}

    def test_invalid_lines_skipped(self):
        assert parse("not-valid-line") == {}


class TestSerialize:
    def test_plain_value(self):
        assert serialize({"KEY": "value"}) == "KEY=value\n"

    def test_value_with_spaces_quoted(self):
        result = serialize({"MSG": "hello world"})
        assert result == 'MSG="hello world"\n'

    def test_value_with_hash_quoted(self):
        result = serialize({"VAL": "foo#bar"})
        assert 'VAL="foo#bar"' in result

    def test_empty_value_quoted(self):
        result = serialize({"EMPTY": ""})
        assert 'EMPTY=""' in result

    def test_round_trip(self):
        original = {
            "APP_ENV": "production",
            "SECRET": "p@ss w0rd!",
            "PORT": "8080",
        }
        assert parse(serialize(original)) == original

    def test_empty_dict_produces_empty_string(self):
        assert serialize({}) == ""


class TestFileIO:
    def test_save_and_load(self, tmp_path: Path):
        env_path = tmp_path / ".env"
        data = {"KEY": "value", "SECRET": "s3cr3t"}
        save_file(env_path, data)
        loaded = load_file(env_path)
        assert loaded == data

    def test_load_file_not_found(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_file(tmp_path / "nonexistent.env")
