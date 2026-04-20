"""CLI command handlers for the priority feature."""

from __future__ import annotations

import argparse
from typing import Any

from envoy_cli.sync import SyncManager
from envoy_cli.priority import (
    PriorityError,
    PRIORITY_LEVELS,
    set_priority,
    remove_priority,
    get_priority,
    list_by_priority,
)


def _make_manager(args: argparse.Namespace) -> SyncManager:
    return SyncManager(
        env=args.env,
        passphrase=args.passphrase,
        base_dir=getattr(args, "base_dir", "."),
    )


def cmd_priority_set(args: argparse.Namespace) -> str:
    """Set priority level for a key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = set_priority(vault.secrets, args.key, args.level)
    except PriorityError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Priority for {args.key!r} set to '{args.level}'."


def cmd_priority_remove(args: argparse.Namespace) -> str:
    """Remove priority metadata from a key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = remove_priority(vault.secrets, args.key)
    except PriorityError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Priority removed from {args.key!r}."


def cmd_priority_get(args: argparse.Namespace) -> str:
    """Show the priority level of a key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        level = get_priority(vault.secrets, args.key)
    except PriorityError as exc:
        raise SystemExit(str(exc)) from exc
    if level is None:
        return f"{args.key!r} has no priority set."
    return f"{args.key!r} priority: {level}"


def cmd_priority_list(args: argparse.Namespace) -> str:
    """List all keys sorted by priority."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    items = list_by_priority(vault.secrets)
    if not items:
        return "No secrets found."
    lines = [f"{key}: {level}" for key, level in items]
    return "\n".join(lines)
