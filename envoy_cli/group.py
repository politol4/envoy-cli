"""Group secrets under logical labels for bulk operations."""

from __future__ import annotations

from typing import Dict, List

GROUP_PREFIX = "__group__"


class GroupError(Exception):
    """Raised when a group operation fails."""


def _meta_key(group_name: str) -> str:
    return f"{GROUP_PREFIX}{group_name}"


def create_group(secrets: Dict[str, str], group_name: str, keys: List[str]) -> Dict[str, str]:
    """Create or overwrite a group with the given keys."""
    if not group_name or not group_name.strip():
        raise GroupError("Group name must not be empty.")
    missing = [k for k in keys if k not in secrets]
    if missing:
        raise GroupError(f"Keys not found in vault: {', '.join(missing)}")
    updated = dict(secrets)
    updated[_meta_key(group_name)] = ",".join(sorted(set(keys)))
    return updated


def delete_group(secrets: Dict[str, str], group_name: str) -> Dict[str, str]:
    """Remove a group definition (does not delete member keys)."""
    key = _meta_key(group_name)
    if key not in secrets:
        raise GroupError(f"Group '{group_name}' does not exist.")
    updated = dict(secrets)
    del updated[key]
    return updated


def get_group_keys(secrets: Dict[str, str], group_name: str) -> List[str]:
    """Return the list of keys belonging to a group."""
    key = _meta_key(group_name)
    if key not in secrets:
        raise GroupError(f"Group '{group_name}' does not exist.")
    raw = secrets[key]
    return [k for k in raw.split(",") if k]


def list_groups(secrets: Dict[str, str]) -> List[str]:
    """Return all group names defined in the vault."""
    names = []
    for k in secrets:
        if k.startswith(GROUP_PREFIX):
            names.append(k[len(GROUP_PREFIX):])
    return sorted(names)


def get_group_secrets(secrets: Dict[str, str], group_name: str) -> Dict[str, str]:
    """Return a mapping of key->value for every member of the group."""
    keys = get_group_keys(secrets, group_name)
    missing = [k for k in keys if k not in secrets]
    if missing:
        raise GroupError(f"Group member keys missing from vault: {', '.join(missing)}")
    return {k: secrets[k] for k in keys}
