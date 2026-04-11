"""CLI commands for vault key access control."""
from __future__ import annotations

import argparse
from typing import Any

from envoy_cli.sync import SyncManager
from envoy_cli import access as ac


def _make_manager(args: Any) -> SyncManager:
    passphrase = getattr(args, "passphrase", "")
    env = getattr(args, "env", "local")
    return SyncManager(passphrase=passphrase, env=env)


def cmd_access_set(args: Any) -> str:
    """Grant *role* to *user* on *key* in the vault."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = ac.set_access(vault.secrets, args.key, args.role, args.user)
    except ac.AccessError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Access granted: {args.user} -> {args.role} on '{args.key}'."


def cmd_access_remove(args: Any) -> str:
    """Revoke *user*'s access entry for *key*."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = ac.remove_access(vault.secrets, args.key, args.user)
    except ac.AccessError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Access removed: '{args.user}' no longer has access to '{args.key}'."


def cmd_access_show(args: Any) -> str:
    """Show the ACL for *key*."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    acl = ac.get_access(vault.secrets, args.key)
    if not acl:
        return f"No access entries for '{args.key}'."
    lines = [f"Access control list for '{args.key}':"]
    for user, role in sorted(acl.items()):
        lines.append(f"  {user}: {role}")
    return "\n".join(lines)


def cmd_access_check(args: Any) -> str:
    """Check whether *user* holds *role* (or higher) on *key*."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    allowed = ac.check_access(vault.secrets, args.key, args.user, args.role)
    status = "ALLOWED" if allowed else "DENIED"
    return f"Access {status}: '{args.user}' / '{args.role}' on '{args.key}'."


def cmd_access_list_user(args: Any) -> str:
    """List all keys that *user* has access to."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    keys = ac.list_user_keys(vault.secrets, args.user)
    if not keys:
        return f"No access entries found for user '{args.user}'."
    lines = [f"Keys accessible by '{args.user}':"]
    for k in keys:
        role = ac.get_access(vault.secrets, k).get(args.user, "?")
        lines.append(f"  {k}: {role}")
    return "\n".join(lines)
