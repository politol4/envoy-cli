"""Redact secrets from arbitrary text or log output."""
from __future__ import annotations

from typing import Dict, List

from envoy_cli.vault import Vault


class RedactError(Exception):
    """Raised when redaction cannot be performed."""


REDACTED_PLACEHOLDER = "[REDACTED]"
_MIN_SECRET_LEN = 3  # secrets shorter than this are too risky to blanket-replace


def _collect_values(secrets: Dict[str, str]) -> List[str]:
    """Return secret values sorted longest-first to avoid partial replacements."""
    values = [
        v for v in secrets.values()
        if isinstance(v, str) and len(v) >= _MIN_SECRET_LEN
    ]
    return sorted(values, key=len, reverse=True)


def redact_text(text: str, secrets: Dict[str, str]) -> str:
    """Replace every occurrence of a secret value in *text* with the placeholder.

    Args:
        text: The raw string that may contain secret values.
        secrets: Mapping of key -> plaintext value (already decrypted).

    Returns:
        A copy of *text* with all secret values replaced.
    """
    if not text:
        return text
    for value in _collect_values(secrets):
        text = text.replace(value, REDACTED_PLACEHOLDER)
    return text


def redact_from_vault(
    text: str,
    vault: Vault,
    passphrase: str,
    env: str,
) -> str:
    """Convenience wrapper that decrypts the vault and redacts *text*.

    Args:
        text: Input string to sanitise.
        vault: Loaded :class:`Vault` instance.
        passphrase: Passphrase used to decrypt vault entries.
        env: Environment name whose secrets should be used.

    Returns:
        Redacted copy of *text*.

    Raises:
        RedactError: If the environment does not exist in the vault.
    """
    envs = vault.list_envs() if hasattr(vault, "list_envs") else []
    secrets_raw = vault.get_all(env, passphrase)  # type: ignore[attr-defined]
    if secrets_raw is None:
        raise RedactError(f"Environment '{env}' not found in vault.")
    return redact_text(text, secrets_raw)
