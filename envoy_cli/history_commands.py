"""CLI command handlers for secret history."""
from __future__ import annotations

import os
from argparse import Namespace
from datetime import datetime, timezone
from typing import Optional

from .history import History


def _history_path(args: Namespace) -> str:
    base = getattr(args, "vault_dir", ".")
    env = getattr(args, "env", "default")
    return os.path.join(base, f".envoy_history_{env}.jsonl")


def _fmt_ts(ts: float) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def cmd_history_list(args: Namespace) -> str:
    history = History(_history_path(args))
    key_filter: Optional[str] = getattr(args, "key", None)
    env_filter: Optional[str] = getattr(args, "env", None)
    entries = history.entries(env=env_filter, key=key_filter)
    if not entries:
        return "No history entries found."
    lines = []
    for e in entries:
        note_part = f" ({e.note})" if e.note else ""
        lines.append(f"[{_fmt_ts(e.timestamp)}] {e.action.upper()} {e.key} env={e.env} actor={e.actor}{note_part}")
    return "\n".join(lines)


def cmd_history_clear(args: Namespace) -> str:
    history = History(_history_path(args))
    count = history.clear()
    env = getattr(args, "env", "default")
    return f"Cleared {count} history entries for env '{env}'."


def cmd_history_show_key(args: Namespace) -> str:
    history = History(_history_path(args))
    key: str = args.key
    env_filter: Optional[str] = getattr(args, "env", None)
    entries = history.entries(env=env_filter, key=key)
    if not entries:
        return f"No history found for key '{key}'."
    lines = [f"History for '{key}':"]
    for e in entries:
        note_part = f" — {e.note}" if e.note else ""
        lines.append(f"  {_fmt_ts(e.timestamp)}  {e.action.upper()}  actor={e.actor}{note_part}")
    return "\n".join(lines)
