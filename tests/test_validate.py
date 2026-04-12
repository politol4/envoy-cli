"""Tests for envoy_cli.validate."""

import pytest

from envoy_cli.validate import (
    ValidateError,
    ValidationReport,
    ValidationWarning,
    validate_secrets,
)


# ---------------------------------------------------------------------------
# ValidationWarning
# ---------------------------------------------------------------------------

class TestValidationWarning:
    def test_to_dict_contains_required_fields(self):
        w = ValidationWarning(key="FOO", message="bad")
        d = w.to_dict()
        assert d["key"] == "FOO"
        assert d["message"] == "bad"

    def test_from_dict_round_trip(self):
        w = ValidationWarning(key="BAR", message="empty")
        assert ValidationWarning.from_dict(w.to_dict()) == w

    def test_from_dict_missing_field_raises(self):
        with pytest.raises(KeyError):
            ValidationWarning.from_dict({"key": "X"})


# ---------------------------------------------------------------------------
# ValidationReport
# ---------------------------------------------------------------------------

class TestValidationReport:
    def test_is_valid_when_no_warnings(self):
        assert ValidationReport().is_valid is True

    def test_not_valid_with_warnings(self):
        r = ValidationReport(warnings=[ValidationWarning(key="K", message="m")])
        assert r.is_valid is False

    def test_summary_all_valid(self):
        assert "valid" in ValidationReport().summary().lower()

    def test_summary_lists_warnings(self):
        r = ValidationReport(warnings=[ValidationWarning(key="K", message="oops")])
        assert "K" in r.summary()
        assert "oops" in r.summary()

    def test_as_lines_empty_when_valid(self):
        assert ValidationReport().as_lines() == []

    def test_as_lines_one_per_warning(self):
        r = ValidationReport(warnings=[
            ValidationWarning(key="A", message="x"),
            ValidationWarning(key="B", message="y"),
        ])
        assert len(r.as_lines()) == 2


# ---------------------------------------------------------------------------
# validate_secrets
# ---------------------------------------------------------------------------

class TestValidateSecrets:
    def test_valid_secrets_returns_clean_report(self):
        report = validate_secrets({"DB_HOST": "localhost", "PORT": "5432"})
        assert report.is_valid

    def test_invalid_key_characters_flagged(self):
        report = validate_secrets({"INVALID KEY": "value"})
        assert not report.is_valid
        assert any("invalid characters" in w.message.lower() for w in report.warnings)

    def test_empty_value_flagged_by_default(self):
        report = validate_secrets({"EMPTY": ""})
        assert not report.is_valid
        assert any("empty" in w.message.lower() for w in report.warnings)

    def test_empty_value_allowed_when_flag_set(self):
        report = validate_secrets({"EMPTY": ""}, allow_empty_values=True)
        assert report.is_valid

    def test_key_too_long_flagged(self):
        long_key = "A" * 200
        report = validate_secrets({long_key: "v"})
        assert any("exceeds" in w.message for w in report.warnings)

    def test_value_too_long_flagged(self):
        report = validate_secrets({"KEY": "x" * 70000})
        assert any("exceeds" in w.message for w in report.warnings)

    def test_required_keys_missing_flagged(self):
        report = validate_secrets({"A": "1"}, required_keys=["A", "B"])
        keys = [w.key for w in report.warnings]
        assert "B" in keys
        assert "A" not in keys

    def test_non_dict_raises_validate_error(self):
        with pytest.raises(ValidateError):
            validate_secrets(["not", "a", "dict"])  # type: ignore

    def test_dotted_key_is_valid(self):
        report = validate_secrets({"app.DB_HOST": "localhost"})
        assert report.is_valid

    def test_key_starting_with_digit_flagged(self):
        report = validate_secrets({"1INVALID": "v"})
        assert not report.is_valid
