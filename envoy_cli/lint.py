"""Lint secrets in a vault for common issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy_cli.vault import Vault

# Keys that should never be committed / stored
_FORBIDDEN_PATTERNS = ("password", "secret", "token", "key", "apikey", "api_key")

# Minimum recommended length for sensitive values
_MIN_SECRET_LENGTH = 8

# Values that are clearly placeholders and should not be used in production
_PLACEHOLDER_VALUES = frozenset(("changeme", "todo", "fixme", "xxx", "placeholder"))


class LintError(Exception):
    """Raised when the lint run itself fails (not for individual warnings)."""


@dataclass
class LintWarning:
    key: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"key": self.key, "message": self.message}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "LintWarning":
        return cls(key=data["key"], message=data["message"])


@dataclass
class LintReport:
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def summary(self) -> str:
        if not self.has_warnings:
            return "No issues found."
        lines = [f"{len(self.warnings)} issue(s) found:"]
        for w in self.warnings:
            lines.append(f"  [{w.key}] {w.message}")
        return "\n".join(lines)


def _is_sensitive_key(key: str) -> bool:
    """Return True if *key* matches any known sensitive-field pattern."""
    lower_key = key.lower()
    return any(pat in lower_key for pat in _FORBIDDEN_PATTERNS)


def lint_vault(vault: Vault) -> LintReport:
    """Inspect all secrets in *vault* and return a LintReport."""
    if not isinstance(vault, Vault):
        raise LintError("lint_vault requires a Vault instance")

    warnings: List[LintWarning] = []
    secrets = vault.all()

    for key, value in secrets.items():
        # Skip internal meta keys (e.g. __tags__.*)
        if key.startswith("__"):
            continue

        # Empty value
        if not value or not value.strip():
            warnings.append(LintWarning(key=key, message="Value is empty."))
            continue

        # Placeholder / default value
        if value.strip().lower() in _PLACEHOLDER_VALUES:
            warnings.append(LintWarning(key=key, message="Value looks like a placeholder."))

        # Short value for sensitive key names
        if _is_sensitive_key(key) and len(value) < _MIN_SECRET_LENGTH:
            warnings.append(
                LintWarning(
                    key=key,
                    message=f"Sensitive key has a short value (< {_MIN_SECRET_LENGTH} chars).",
                )
            )

    return LintReport(warnings=warnings)
