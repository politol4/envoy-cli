"""Namespace support: group secrets under a dotted prefix (e.g. DB.HOST)."""

from __future__ import annotations

from typing import Dict, List

SEP = "."


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


def _validate_namespace(ns: str) -> None:
    if not ns or not ns.strip():
        raise NamespaceError("Namespace must be a non-empty string.")
    if SEP in ns:
        raise NamespaceError(
            f"Namespace '{ns}' must not contain '{SEP}'. Use a simple identifier."
        )


def namespace_key(ns: str, key: str) -> str:
    """Return the fully-qualified key for *key* inside *ns*."""
    _validate_namespace(ns)
    if not key or not key.strip():
        raise NamespaceError("Key must be a non-empty string.")
    return f"{ns}{SEP}{key}"


def split_key(full_key: str):
    """Return (namespace, bare_key) or (None, full_key) if un-namespaced."""
    if SEP in full_key:
        ns, _, bare = full_key.partition(SEP)
        return ns, bare
    return None, full_key


def list_namespaces(secrets: Dict[str, str]) -> List[str]:
    """Return a sorted, deduplicated list of namespaces present in *secrets*."""
    ns_set = set()
    for key in secrets:
        ns, _ = split_key(key)
        if ns is not None:
            ns_set.add(ns)
    return sorted(ns_set)


def keys_in_namespace(secrets: Dict[str, str], ns: str) -> Dict[str, str]:
    """Return a dict of bare_key -> value for all keys inside *ns*."""
    _validate_namespace(ns)
    prefix = ns + SEP
    return {
        key[len(prefix):]: value
        for key, value in secrets.items()
        if key.startswith(prefix)
    }


def move_namespace(secrets: Dict[str, str], old_ns: str, new_ns: str) -> Dict[str, str]:
    """Return a copy of *secrets* with all keys in *old_ns* renamed to *new_ns*."""
    _validate_namespace(old_ns)
    _validate_namespace(new_ns)
    if old_ns == new_ns:
        raise NamespaceError(f"Source and destination namespace are both '{old_ns}'.")
    result: Dict[str, str] = {}
    old_prefix = old_ns + SEP
    for key, value in secrets.items():
        if key.startswith(old_prefix):
            bare = key[len(old_prefix):]
            result[namespace_key(new_ns, bare)] = value
        else:
            result[key] = value
    return result
