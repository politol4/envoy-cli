"""CLI command handlers for TTL management."""

from __future__ import annotations

import argparse
import os

from envoy_cli.sync import SyncManager
from envoy_cli.ttl import TTLError, get_ttl, list_expiring, purge_expired, remove_ttl, set_ttl


def _make_manager(args: argparse.Namespace) -> SyncManager:
    passphrase = os.environ.get("ENVOY_PASSPHRASE", "")
    return SyncManager(env=args.env, passphrase=passphrase)


def cmd_ttl_set(args: argparse.Namespace) -> str:
    """Attach a TTL to a secret key."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    try:
        vault.secrets = set_ttl(vault.secrets, args.key, args.seconds)
    except TTLError as exc:
        raise SystemExit(f"ttl-set error: {exc}") from exc
    manager.save_vault(vault)
    return f"TTL of {args.seconds}s set on '{args.key}'."


def cmd_ttl_get(args: argparse.Namespace) -> str:
    """Show remaining TTL for a secret key."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    remaining = get_ttl(vault.secrets, args.key)
    if remaining is None:
        return f"No TTL set for '{args.key}'."
    return f"'{args.key}' expires in {remaining}s."


def cmd_ttl_remove(args: argparse.Namespace) -> str:
    """Remove the TTL from a secret key."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    vault.secrets = remove_ttl(vault.secrets, args.key)
    manager.save_vault(vault)
    return f"TTL removed from '{args.key}'."


def cmd_ttl_purge(args: argparse.Namespace) -> str:
    """Purge all expired secrets from the vault."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    before = {k for k in vault.secrets if not k.startswith("__ttl__")}
    vault.secrets = purge_expired(vault.secrets)
    after = {k for k in vault.secrets if not k.startswith("__ttl__")}
    removed = sorted(before - after)
    manager.save_vault(vault)
    if not removed:
        return "No expired secrets found."
    return "Purged expired keys: " + ", ".join(removed) + "."


def cmd_ttl_list_expiring(args: argparse.Namespace) -> str:
    """List secrets expiring within a given window (default 1 h)."""
    manager = _make_manager(args)
    vault = manager.load_vault()
    keys = list_expiring(vault.secrets, within_seconds=args.within)
    if not keys:
        return f"No secrets expiring within {args.within}s."
    lines = [f"Secrets expiring within {args.within}s:"]
    for key in keys:
        remaining = get_ttl(vault.secrets, key)
        lines.append(f"  {key}: {remaining}s remaining")
    return "\n".join(lines)
