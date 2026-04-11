"""Secret key aliasing — map a friendly alias to an existing vault key."""

from __future__ import annotations

from typing import Dict, List

ALIAS_PREFIX = "__alias__."


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _meta_key(alias: str) -> str:
    return f"{ALIAS_PREFIX}{alias}"


def add_alias(secrets: Dict[str, str], alias: str, target: str) -> Dict[str, str]:
    """Register *alias* as a pointer to *target*.

    Raises AliasError if *target* does not exist, *alias* is already a real
    key, or *alias* already points to a different target.
    """
    if not alias or not alias.strip():
        raise AliasError("Alias name must not be empty.")
    if not target or not target.strip():
        raise AliasError("Target key must not be empty.")
    if target not in secrets:
        raise AliasError(f"Target key '{target}' does not exist in the vault.")
    if alias in secrets and not alias.startswith(ALIAS_PREFIX):
        raise AliasError(f"'{alias}' is already a real secret key; choose a different alias.")
    meta = _meta_key(alias)
    if meta in secrets and secrets[meta] != target:
        raise AliasError(
            f"Alias '{alias}' already points to '{secrets[meta]}'. Remove it first."
        )
    updated = dict(secrets)
    updated[meta] = target
    return updated


def remove_alias(secrets: Dict[str, str], alias: str) -> Dict[str, str]:
    """Remove an alias entry.  Raises AliasError if alias is not registered."""
    meta = _meta_key(alias)
    if meta not in secrets:
        raise AliasError(f"Alias '{alias}' is not registered.")
    updated = dict(secrets)
    del updated[meta]
    return updated


def resolve_alias(secrets: Dict[str, str], alias: str) -> str:
    """Return the value of the key that *alias* points to.

    Raises AliasError if the alias or its target cannot be found.
    """
    meta = _meta_key(alias)
    if meta not in secrets:
        raise AliasError(f"Alias '{alias}' is not registered.")
    target = secrets[meta]
    if target not in secrets:
        raise AliasError(
            f"Alias '{alias}' points to '{target}', but that key no longer exists."
        )
    return secrets[target]


def list_aliases(secrets: Dict[str, str]) -> List[Dict[str, str]]:
    """Return all registered aliases as a list of {alias, target} dicts."""
    result = []
    for key, value in secrets.items():
        if key.startswith(ALIAS_PREFIX):
            result.append({"alias": key[len(ALIAS_PREFIX):], "target": value})
    return sorted(result, key=lambda d: d["alias"])
