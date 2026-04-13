"""Tests for envoy_cli.schema."""
import pytest

from envoy_cli.schema import (
    FieldRule,
    SchemaError,
    SchemaReport,
    SchemaViolation,
    validate_against_schema,
)


# ---------------------------------------------------------------------------
# FieldRule serialisation
# ---------------------------------------------------------------------------

class TestFieldRule:
    def test_to_dict_contains_required_fields(self):
        rule = FieldRule(key="DB_URL", required=True, pattern=r"postgres://.+")
        d = rule.to_dict()
        assert d["key"] == "DB_URL"
        assert d["required"] is True
        assert d["pattern"] == r"postgres://.+"

    def test_from_dict_round_trip(self):
        original = FieldRule(key="SECRET", required=False, min_length=8, max_length=64)
        restored = FieldRule.from_dict(original.to_dict())
        assert restored.key == original.key
        assert restored.required == original.required
        assert restored.min_length == original.min_length
        assert restored.max_length == original.max_length

    def test_from_dict_missing_key_raises(self):
        with pytest.raises(SchemaError):
            FieldRule.from_dict({"required": True})

    def test_defaults_applied(self):
        rule = FieldRule.from_dict({"key": "FOO"})
        assert rule.required is False
        assert rule.pattern is None
        assert rule.min_length == 0
        assert rule.max_length == 0


# ---------------------------------------------------------------------------
# SchemaReport
# ---------------------------------------------------------------------------

class TestSchemaReport:
    def test_is_valid_when_no_violations(self):
        report = SchemaReport()
        assert report.is_valid is True

    def test_is_invalid_when_violations_present(self):
        report = SchemaReport(violations=[SchemaViolation("K", "bad")])
        assert report.is_valid is False

    def test_summary_pass(self):
        assert "passed" in SchemaReport().summary()

    def test_summary_fail_contains_count(self):
        report = SchemaReport(
            violations=[SchemaViolation("A", "msg1"), SchemaViolation("B", "msg2")]
        )
        assert "2" in report.summary()

    def test_summary_fail_contains_key(self):
        report = SchemaReport(violations=[SchemaViolation("MY_KEY", "oops")])
        assert "MY_KEY" in report.summary()


# ---------------------------------------------------------------------------
# validate_against_schema
# ---------------------------------------------------------------------------

class TestValidateAgainstSchema:
    def _secrets(self, **kw):
        return dict(kw)

    def test_returns_schema_report(self):
        result = validate_against_schema({}, [])
        assert isinstance(result, SchemaReport)

    def test_no_rules_always_valid(self):
        report = validate_against_schema({"A": "1", "B": "2"}, [])
        assert report.is_valid

    def test_required_key_present_is_valid(self):
        rules = [FieldRule(key="DB_URL", required=True)]
        report = validate_against_schema({"DB_URL": "postgres://localhost"}, rules)
        assert report.is_valid

    def test_required_key_missing_is_violation(self):
        rules = [FieldRule(key="DB_URL", required=True)]
        report = validate_against_schema({}, rules)
        assert not report.is_valid
        assert report.violations[0].key == "DB_URL"

    def test_optional_key_missing_is_valid(self):
        rules = [FieldRule(key="OPTIONAL", required=False)]
        report = validate_against_schema({}, rules)
        assert report.is_valid

    def test_min_length_violation(self):
        rules = [FieldRule(key="TOKEN", min_length=16)]
        report = validate_against_schema({"TOKEN": "short"}, rules)
        assert not report.is_valid
        assert "too short" in report.violations[0].message

    def test_min_length_ok(self):
        rules = [FieldRule(key="TOKEN", min_length=4)]
        report = validate_against_schema({"TOKEN": "longvalue"}, rules)
        assert report.is_valid

    def test_max_length_violation(self):
        rules = [FieldRule(key="CODE", max_length=4)]
        report = validate_against_schema({"CODE": "toolongvalue"}, rules)
        assert not report.is_valid
        assert "too long" in report.violations[0].message

    def test_pattern_match_is_valid(self):
        rules = [FieldRule(key="PORT", pattern=r"\d+")]
        report = validate_against_schema({"PORT": "5432"}, rules)
        assert report.is_valid

    def test_pattern_mismatch_is_violation(self):
        rules = [FieldRule(key="PORT", pattern=r"\d+")]
        report = validate_against_schema({"PORT": "not-a-number"}, rules)
        assert not report.is_valid
        assert "pattern" in report.violations[0].message

    def test_multiple_violations_collected(self):
        rules = [
            FieldRule(key="A", required=True),
            FieldRule(key="B", required=True),
        ]
        report = validate_against_schema({}, rules)
        assert len(report.violations) == 2
