"""Helpers to integrate History recording into SyncManager operations."""
from __future__ import annotations

import os
from typing import Dict, Optional

from .history import History, HistoryEntry


def _history_for_env(vault_dir: str, env: str) -> History:
    path = os.path.join(vault_dir, f".envoy_history_{env}.jsonl")
    return History(path)


def record_set(
    vault_dir: str,
    env: str,
    key: str,
    actor: str = "local",
    note: str = "",
) -> None:
    """Record a 'set' action for a single key."""
    h = _history_for_env(vault_dir, env)
    h.record(HistoryEntry(action="set", key=key, env=env, actor=actor, note=note))


def record_delete(
    vault_dir: str,
    env: str,
    key: str,
    actor: str = "local",
    note: str = "",
) -> None:
    """Record a 'delete' action for a single key."""
    h = _history_for_env(vault_dir, env)
    h.record(HistoryEntry(action="delete", key=key, env=env, actor=actor, note=note))


def record_rotation(
    vault_dir: str,
    env: str,
    keys: list,
    actor: str = "local",
    note: str = "key rotation",
) -> None:
    """Record a 'rotate' action for every affected key."""
    h = _history_for_env(vault_dir, env)
    for key in keys:
        h.record(HistoryEntry(action="rotate", key=key, env=env, actor=actor, note=note))


def record_import(
    vault_dir: str,
    env: str,
    secrets: Dict[str, str],
    actor: str = "local",
    note: str = "imported",
) -> None:
    """Record a 'set' action for each key in an imported secrets dict."""
    h = _history_for_env(vault_dir, env)
    for key in secrets:
        h.record(HistoryEntry(action="set", key=key, env=env, actor=actor, note=note))
