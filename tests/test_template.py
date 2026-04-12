"""Tests for envoy_cli.template."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from envoy_cli.template import TemplateError, render, render_from_vault


class TestRender(unittest.TestCase):
    def test_simple_substitution(self):
        result = render("Hello {{ NAME }}", {"NAME": "world"})
        self.assertEqual(result, "Hello world")

    def test_multiple_placeholders(self):
        tmpl = "{{ HOST }}:{{ PORT }}/{{ DB }}"
        secrets = {"HOST": "localhost", "PORT": "5432", "DB": "mydb"}
        self.assertEqual(render(tmpl, secrets), "localhost:5432/mydb")

    def test_placeholder_with_extra_spaces(self):
        result = render("{{  KEY  }}", {"KEY": "value"})
        self.assertEqual(result, "value")

    def test_no_placeholders_returns_original(self):
        tmpl = "no placeholders here"
        self.assertEqual(render(tmpl, {}), tmpl)

    def test_strict_missing_key_raises(self):
        with self.assertRaises(TemplateError) as ctx:
            render("{{ MISSING }}", {}, strict=True)
        self.assertIn("MISSING", str(ctx.exception))

    def test_strict_reports_all_missing_keys(self):
        with self.assertRaises(TemplateError) as ctx:
            render("{{ A }} {{ B }}", {}, strict=True)
        msg = str(ctx.exception)
        self.assertIn("A", msg)
        self.assertIn("B", msg)

    def test_non_strict_leaves_missing_placeholder(self):
        result = render("{{ MISSING }}", {}, strict=False)
        self.assertEqual(result, "{{ MISSING }}")

    def test_non_strict_substitutes_known_keeps_unknown(self):
        result = render("{{ KNOWN }} {{ UNKNOWN }}", {"KNOWN": "hi"}, strict=False)
        self.assertEqual(result, "hi {{ UNKNOWN }}")

    def test_repeated_placeholder_replaced_each_time(self):
        result = render("{{ X }}-{{ X }}", {"X": "42"})
        self.assertEqual(result, "42-42")

    def test_numeric_suffix_in_key(self):
        result = render("{{ VAR_1 }}", {"VAR_1": "one"})
        self.assertEqual(result, "one")

    def test_invalid_placeholder_not_matched(self):
        # Keys starting with a digit should not be matched
        tmpl = "{{ 1INVALID }}"
        result = render(tmpl, {"1INVALID": "x"}, strict=False)
        self.assertEqual(result, tmpl)

    def test_empty_template_returns_empty_string(self):
        self.assertEqual(render("", {}), "")

    def test_value_containing_braces_is_substituted_literally(self):
        # The substituted value should not be interpreted as another placeholder
        result = render("{{ VAL }}", {"VAL": "{{ OTHER }}"})
        self.assertEqual(result, "{{ OTHER }}")


class TestRenderFromVault(unittest.TestCase):
    def _make_vault(self, secrets):
        vault = MagicMock()
        vault.get_all = MagicMock(return_value=secrets)
        return vault

    def test_calls_get_all_with_passphrase(self):
        vault = self._make_vault({"K": "v"})
        render_from_vault("{{ K }}", vault, "pass")
        vault.get_all.assert_called_once_with("pass")

    def test_returns_rendered_string(self):
        vault = self._make_vault({"API_KEY": "secret123"})
        result = render_from_vault("key={{ API_KEY }}", vault, "pass")
        self.assertEqual(result, "key=secret123")

    def test_strict_propagated(self):
        vault = self._make_vault({})
        with self.assertRaises(TemplateError):
            render_from_vault("{{ MISSING }}", vault, "pass", strict=True)
