"""Template rendering: substitute vault secrets into a template string."""

from __future__ import annotations

import re
from typing import Dict

from envoy_cli.vault import Vault

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


def render(template: str, secrets: Dict[str, str], *, strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *secrets*.

    Parameters
    ----------
    template:
        Raw template text containing ``{{ KEY }}`` placeholders.
    secrets:
        Mapping of key -> plaintext value used for substitution.
    strict:
        When ``True`` (default) any placeholder whose key is absent from
        *secrets* raises :class:`TemplateError`.  When ``False`` the
        placeholder is left unchanged.

    Returns
    -------
    str
        The rendered string with all resolvable placeholders replaced.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in secrets:
            return secrets[key]
        if strict:
            missing.append(key)
            return match.group(0)  # keep original so we can report all at once
        return match.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template)

    if strict and missing:
        raise TemplateError(
            "Template references undefined secret(s): " + ", ".join(sorted(missing))
        )

    return result


def render_from_vault(
    template: str,
    vault: Vault,
    passphrase: str,
    *,
    strict: bool = True,
) -> str:
    """Convenience wrapper that decrypts *vault* and calls :func:`render`."""
    secrets = vault.get_all(passphrase)
    return render(template, secrets, strict=strict)
