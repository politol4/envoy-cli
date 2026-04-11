"""Role-based access control for vault keys."""
from __future__ import annotations

from typing import Dict, List, Optional

ACCESS_META_PREFIX = "__access__"

VALID_ROLES = {"read", "write", "admin"}


class AccessError(Exception):
    """Raised when an access-control operation fails."""


def _meta_key(key: str) -> str:
    return f"{ACCESS_META_PREFIX}{key}"


def set_access(secrets: Dict[str, str], key: str, role: str, user: str) -> Dict[str, str]:
    """Assign *role* to *user* for *key*. Returns updated secrets copy."""
    if key not in secrets:
        raise AccessError(f"Key '{key}' not found in vault.")
    if role not in VALID_ROLES:
        raise AccessError(f"Invalid role '{role}'. Must be one of: {sorted(VALID_ROLES)}.")
    if not user or not user.strip():
        raise AccessError("User must be a non-empty string.")

    updated = dict(secrets)
    meta_k = _meta_key(key)
    existing = _parse_acl(updated.get(meta_k, ""))
    existing[user.strip()] = role
    updated[meta_k] = _serialize_acl(existing)
    return updated


def remove_access(secrets: Dict[str, str], key: str, user: str) -> Dict[str, str]:
    """Remove *user*'s access entry for *key*."""
    meta_k = _meta_key(key)
    updated = dict(secrets)
    existing = _parse_acl(updated.get(meta_k, ""))
    if user not in existing:
        raise AccessError(f"User '{user}' has no access entry for key '{key}'.")
    del existing[user]
    if existing:
        updated[meta_k] = _serialize_acl(existing)
    else:
        updated.pop(meta_k, None)
    return updated


def get_access(secrets: Dict[str, str], key: str) -> Dict[str, str]:
    """Return mapping of user -> role for *key*."""
    meta_k = _meta_key(key)
    return _parse_acl(secrets.get(meta_k, ""))


def check_access(secrets: Dict[str, str], key: str, user: str, required_role: str) -> bool:
    """Return True if *user* holds at least *required_role* for *key*."""
    role_order = ["read", "write", "admin"]
    acl = get_access(secrets, key)
    user_role = acl.get(user)
    if user_role is None:
        return False
    return role_order.index(user_role) >= role_order.index(required_role)


def list_user_keys(secrets: Dict[str, str], user: str) -> List[str]:
    """Return list of keys that *user* has any access entry for."""
    result = []
    for k, v in secrets.items():
        if k.startswith(ACCESS_META_PREFIX):
            acl = _parse_acl(v)
            if user in acl:
                result.append(k[len(ACCESS_META_PREFIX):])
    return sorted(result)


def _parse_acl(raw: str) -> Dict[str, str]:
    if not raw:
        return {}
    pairs: Dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if ":" in part:
            u, r = part.split(":", 1)
            pairs[u.strip()] = r.strip()
    return pairs


def _serialize_acl(acl: Dict[str, str]) -> str:
    return ",".join(f"{u}:{r}" for u, r in sorted(acl.items()))
