"""CLI command handlers for retention policy management."""
from __future__ import annotations

import argparse
import time

from envoy_cli.sync import SyncManager
from envoy_cli.retention import (
    RetentionError,
    set_retention,
    remove_retention,
    get_retention,
    find_expired,
    purge_expired,
)


def _make_manager(args: argparse.Namespace) -> SyncManager:
    return SyncManager(env=args.env, passphrase=args.passphrase, base_dir=getattr(args, "base_dir", "."))


def cmd_retention_set(args: argparse.Namespace) -> str:
    """Set a retention policy of *days* days on *key*."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    try:
        vault.secrets = set_retention(vault.secrets, args.key, args.days)
    except RetentionError as exc:
        raise SystemExit(str(exc)) from exc
    manager.save_vault(vault)
    return f"Retention policy of {args.days} day(s) set for '{args.key}'."


def cmd_retention_remove(args: argparse.Namespace) -> str:
    """Remove the retention policy from *key*."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    try:
        vault.secrets = remove_retention(vault.secrets, args.key)
    except RetentionError as exc:
        raise SystemExit(str(exc)) from exc
    manager.save_vault(vault)
    return f"Retention policy removed from '{args.key}'."


def cmd_retention_get(args: argparse.Namespace) -> str:
    """Show the retention policy for *key*."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    info = get_retention(vault.secrets, args.key)
    if info is None:
        return f"No retention policy set for '{args.key}'."
    days, created_at = info
    age_days = (time.time() - created_at) / 86400
    return (
        f"Key: {args.key}\n"
        f"Retention: {days} day(s)\n"
        f"Age: {age_days:.1f} day(s)"
    )


def cmd_retention_list(args: argparse.Namespace) -> str:
    """List all keys that have an expiry date and their status."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    now = time.time()
    lines = []
    for key, value in sorted(vault.secrets.items()):
        if key.startswith("__retention__"):
            continue
        info = get_retention(vault.secrets, key)
        if info is None:
            continue
        days, created_at = info
        age_days = (now - created_at) / 86400
        status = "EXPIRED" if age_days >= days else "ok"
        lines.append(f"{key}: {days}d retention, {age_days:.1f}d old [{status}]")
    return "\n".join(lines) if lines else "No retention policies configured."


def cmd_retention_purge(args: argparse.Namespace) -> str:
    """Remove all secrets whose retention period has elapsed."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    expired = find_expired(vault.secrets)
    if not expired:
        return "No expired secrets found."
    vault.secrets = purge_expired(vault.secrets)
    manager.save_vault(vault)
    keys_str = ", ".join(f"'{k}'" for k in expired)
    return f"Purged {len(expired)} expired secret(s): {keys_str}."
