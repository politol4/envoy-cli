"""Schema validation for secret keys and values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SchemaError(Exception):
    """Raised when a schema definition is invalid."""


@dataclass
class FieldRule:
    """Validation rule for a single secret key."""

    key: str
    required: bool = False
    pattern: Optional[str] = None
    min_length: int = 0
    max_length: int = 0  # 0 means unlimited

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "required": self.required,
            "pattern": self.pattern,
            "min_length": self.min_length,
            "max_length": self.max_length,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FieldRule":
        for f in ("key",):
            if f not in data:
                raise SchemaError(f"FieldRule missing required field: {f!r}")
        return cls(
            key=data["key"],
            required=bool(data.get("required", False)),
            pattern=data.get("pattern"),
            min_length=int(data.get("min_length", 0)),
            max_length=int(data.get("max_length", 0)),
        )


@dataclass
class SchemaViolation:
    key: str
    message: str

    def to_dict(self) -> dict:
        return {"key": self.key, "message": self.message}


@dataclass
class SchemaReport:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "Schema validation passed."
        lines = [f"Schema validation failed with {len(self.violations)} violation(s):"]
        for v in self.violations:
            lines.append(f"  [{v.key}] {v.message}")
        return "\n".join(lines)


def validate_against_schema(
    secrets: Dict[str, str], rules: List[FieldRule]
) -> SchemaReport:
    """Validate *secrets* against the list of *rules*."""
    violations: List[SchemaViolation] = []

    for rule in rules:
        value = secrets.get(rule.key)

        if value is None:
            if rule.required:
                violations.append(
                    SchemaViolation(rule.key, "required key is missing")
                )
            continue

        if rule.min_length and len(value) < rule.min_length:
            violations.append(
                SchemaViolation(
                    rule.key,
                    f"value too short (min {rule.min_length}, got {len(value)})",
                )
            )

        if rule.max_length and len(value) > rule.max_length:
            violations.append(
                SchemaViolation(
                    rule.key,
                    f"value too long (max {rule.max_length}, got {len(value)})",
                )
            )

        if rule.pattern and not re.fullmatch(rule.pattern, value):
            violations.append(
                SchemaViolation(
                    rule.key,
                    f"value does not match pattern {rule.pattern!r}",
                )
            )

    return SchemaReport(violations=violations)
