"""compliance.py — Check secrets against compliance rules (e.g. naming conventions,
required keys, forbidden patterns) and produce a structured report."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ComplianceError(Exception):
    """Raised when compliance configuration is invalid."""


@dataclass
class ComplianceViolation:
    """A single compliance rule violation."""

    key: str
    rule: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "rule": self.rule,
            "message": self.message,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ComplianceViolation":
        for f in ("key", "rule", "message"):
            if f not in data:
                raise ComplianceError(f"Missing field '{f}' in ComplianceViolation")
        return cls(
            key=data["key"],
            rule=data["rule"],
            message=data["message"],
            severity=data.get("severity", "error"),
        )


@dataclass
class ComplianceReport:
    """Aggregated result of a compliance check."""

    violations: List[ComplianceViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return bool(self.violations)

    @property
    def errors(self) -> List[ComplianceViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> List[ComplianceViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    def summary(self) -> str:
        if not self.has_violations:
            return "All compliance checks passed."
        parts = []
        if self.errors:
            parts.append(f"{len(self.errors)} error(s)")
        if self.warnings:
            parts.append(f"{len(self.warnings)} warning(s)")
        return "Compliance issues found: " + ", ".join(parts) + "."

    def as_lines(self) -> List[str]:
        lines = []
        for v in sorted(self.violations, key=lambda x: (x.severity, x.key)):
            tag = "[ERROR]" if v.severity == "error" else "[WARN] "
            lines.append(f"{tag} {v.key}: [{v.rule}] {v.message}")
        return lines


def check_compliance(
    secrets: Dict[str, str],
    *,
    required_keys: Optional[List[str]] = None,
    key_pattern: Optional[str] = None,
    forbidden_value_patterns: Optional[List[str]] = None,
    max_value_length: Optional[int] = None,
) -> ComplianceReport:
    """Run compliance rules against a secrets dict and return a report.

    Args:
        secrets: Mapping of secret key -> value.
        required_keys: Keys that must be present.
        key_pattern: Regex that every key must match (e.g. ``^[A-Z0-9_]+$``).
        forbidden_value_patterns: List of regexes; values must not match any.
        max_value_length: Maximum allowed length for any value.

    Returns:
        A :class:`ComplianceReport` with all detected violations.
    """
    report = ComplianceReport()

    # 1. Required keys
    for req in required_keys or []:
        if req not in secrets:
            report.violations.append(
                ComplianceViolation(
                    key=req,
                    rule="required_key",
                    message=f"Required key '{req}' is missing.",
                    severity="error",
                )
            )

    compiled_key_re = re.compile(key_pattern) if key_pattern else None
    compiled_forbidden = [
        re.compile(p) for p in (forbidden_value_patterns or [])
    ]

    for key, value in secrets.items():
        # 2. Key naming convention
        if compiled_key_re and not compiled_key_re.match(key):
            report.violations.append(
                ComplianceViolation(
                    key=key,
                    rule="key_pattern",
                    message=(
                        f"Key '{key}' does not match required pattern "
                        f"'{key_pattern}'."
                    ),
                    severity="warning",
                )
            )

        # 3. Forbidden value patterns
        for pattern in compiled_forbidden:
            if pattern.search(value):
                report.violations.append(
                    ComplianceViolation(
                        key=key,
                        rule="forbidden_value_pattern",
                        message=(
                            f"Value for '{key}' matches forbidden pattern "
                            f"'{pattern.pattern}'."
                        ),
                        severity="error",
                    )
                )
                break  # one violation per key per category is enough

        # 4. Max value length
        if max_value_length is not None and len(value) > max_value_length:
            report.violations.append(
                ComplianceViolation(
                    key=key,
                    rule="max_value_length",
                    message=(
                        f"Value for '{key}' exceeds max length "
                        f"({len(value)} > {max_value_length})."
                    ),
                    severity="warning",
                )
            )

    return report
