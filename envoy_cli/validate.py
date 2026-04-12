"""Validation rules for secret keys and values in a vault."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_.\-]*$')
_MAX_KEY_LEN = 128
_MAX_VALUE_LEN = 65536


class ValidateError(Exception):
    """Raised when validation cannot proceed (e.g. empty secrets)."""


@dataclass
class ValidationWarning:
    key: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key, "message": self.message}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ValidationWarning":
        for f in ("key", "message"):
            if f not in data:
                raise KeyError(f"Missing field: {f}")
        return cls(key=data["key"], message=data["message"])


@dataclass
class ValidationReport:
    warnings: List[ValidationWarning] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.warnings) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "All secrets are valid."
        lines = [f"  [{w.key}] {w.message}" for w in self.warnings]
        return "Validation warnings:\n" + "\n".join(lines)

    def as_lines(self) -> List[str]:
        return [f"{w.key}: {w.message}" for w in self.warnings]


def validate_secrets(
    secrets: Dict[str, str],
    *,
    allow_empty_values: bool = False,
    required_keys: Optional[List[str]] = None,
) -> ValidationReport:
    """Validate all key/value pairs in *secrets* and return a report."""
    if not isinstance(secrets, dict):
        raise ValidateError("secrets must be a dict")

    warnings: List[ValidationWarning] = []

    for key, value in secrets.items():
        if not _KEY_RE.match(key):
            warnings.append(ValidationWarning(key=key, message="Key contains invalid characters"))
        if len(key) > _MAX_KEY_LEN:
            warnings.append(ValidationWarning(key=key, message=f"Key exceeds {_MAX_KEY_LEN} characters"))
        if not allow_empty_values and value == "":
            warnings.append(ValidationWarning(key=key, message="Value is empty"))
        if len(value) > _MAX_VALUE_LEN:
            warnings.append(ValidationWarning(key=key, message=f"Value exceeds {_MAX_VALUE_LEN} characters"))

    for req in (required_keys or []):
        if req not in secrets:
            warnings.append(ValidationWarning(key=req, message="Required key is missing"))

    return ValidationReport(warnings=warnings)
