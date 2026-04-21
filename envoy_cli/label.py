"""Label management for vault secrets.

Labels are free-form string tags attached to a key for categorisation,
filtering, and documentation purposes.  Unlike tags (which are stored as
a comma-separated list in a single meta key), labels use a dedicated
JSON-encoded meta key so that arbitrary string values (including commas)
are supported safely.
"""

from __future__ import annotations

import json
from typing import Dict, List

META_SUFFIX = ".__labels__"


class LabelError(Exception):
    """Raised when a label operation fails."""


def _meta_key(key: str) -> str:
    return f"{key}{META_SUFFIX}"


def add_label(secrets: Dict[str, str], key: str, label: str) -> Dict[str, str]:
    """Return a new secrets dict with *label* added to *key*."""
    if key not in secrets:
        raise LabelError(f"Key '{key}' does not exist.")
    if not label or not label.strip():
        raise LabelError("Label must be a non-empty string.")
    label = label.strip()
    updated = dict(secrets)
    meta = _meta_key(key)
    existing = _get_labels_from_dict(secrets, key)
    if label not in existing:
        existing.append(label)
    updated[meta] = json.dumps(sorted(existing))
    return updated


def remove_label(secrets: Dict[str, str], key: str, label: str) -> Dict[str, str]:
    """Return a new secrets dict with *label* removed from *key*."""
    if key not in secrets:
        raise LabelError(f"Key '{key}' does not exist.")
    existing = _get_labels_from_dict(secrets, key)
    if label not in existing:
        raise LabelError(f"Label '{label}' is not set on '{key}'.")
    existing.remove(label)
    updated = dict(secrets)
    meta = _meta_key(key)
    if existing:
        updated[meta] = json.dumps(sorted(existing))
    else:
        updated.pop(meta, None)
    return updated


def _get_labels_from_dict(secrets: Dict[str, str], key: str) -> List[str]:
    meta = _meta_key(key)
    raw = secrets.get(meta)
    if not raw:
        return []
    try:
        return list(json.loads(raw))
    except (json.JSONDecodeError, TypeError):
        return []


def get_labels(secrets: Dict[str, str], key: str) -> List[str]:
    """Return the list of labels attached to *key*."""
    if key not in secrets:
        raise LabelError(f"Key '{key}' does not exist.")
    return _get_labels_from_dict(secrets, key)


def list_labeled(secrets: Dict[str, str], label: str) -> List[str]:
    """Return all secret keys that carry *label*."""
    result = []
    for key in secrets:
        if key.endswith(META_SUFFIX):
            continue
        if label in _get_labels_from_dict(secrets, key):
            result.append(key)
    return sorted(result)
