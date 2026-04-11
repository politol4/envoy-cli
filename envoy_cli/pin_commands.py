"""CLI command handlers for secret pinning."""

from __future__ import annotations

import argparse
import os

from envoy_cli.pin import PinError, list_pinned, pin_key, unpin_key, is_pinned
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


def _make_manager(args: argparse.Namespace) -> SyncManager:
    profile = getattr(args, "profile", "default")
    env = getattr(args, "env", "development")
    return SyncManager(profile=profile, env=env)


def cmd_pin_set(args: argparse.Namespace) -> str:
    """Pin a secret key so it cannot be overwritten by push/pull."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    try:
        vault.secrets = pin_key(vault.secrets, args.key)
    except PinError as exc:
        raise PinError(str(exc)) from exc
    vault.save(args.passphrase)
    return f"Key '{args.key}' is now pinned."


def cmd_pin_remove(args: argparse.Namespace) -> str:
    """Unpin a previously pinned secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    try:
        vault.secrets = unpin_key(vault.secrets, args.key)
    except PinError as exc:
        raise PinError(str(exc)) from exc
    vault.save(args.passphrase)
    return f"Key '{args.key}' has been unpinned."


def cmd_pin_list(args: argparse.Namespace) -> str:
    """List all pinned keys in the vault."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    pinned = list_pinned(vault.secrets)
    if not pinned:
        return "No pinned keys."
    lines = ["Pinned keys:"]
    lines.extend(f"  - {k}" for k in pinned)
    return "\n".join(lines)


def cmd_pin_status(args: argparse.Namespace) -> str:
    """Show whether a specific key is pinned."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    if args.key not in vault.secrets:
        raise PinError(f"Key '{args.key}' does not exist.")
    status = "pinned" if is_pinned(vault.secrets, args.key) else "not pinned"
    return f"Key '{args.key}' is {status}."
