"""CLI command handlers for group management."""

from __future__ import annotations

from typing import Any

from envoy_cli.group import (
    GroupError,
    create_group,
    delete_group,
    get_group_keys,
    get_group_secrets,
    list_groups,
)
from envoy_cli.sync import SyncManager


def _make_manager(args: Any) -> SyncManager:
    return SyncManager(
        env=args.env,
        passphrase=args.passphrase,
        vault_dir=getattr(args, "vault_dir", "."),
    )


def cmd_group_create(args: Any) -> str:
    """Create or overwrite a group with a list of keys."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    updated = create_group(vault.secrets, args.group, keys)
    vault.secrets = updated
    mgr._save_vault(vault)
    return f"Group '{args.group}' created with {len(keys)} key(s)."


def cmd_group_delete(args: Any) -> str:
    """Remove a group definition."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    updated = delete_group(vault.secrets, args.group)
    vault.secrets = updated
    mgr._save_vault(vault)
    return f"Group '{args.group}' deleted."


def cmd_group_list(args: Any) -> str:
    """List all groups in the vault."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    groups = list_groups(vault.secrets)
    if not groups:
        return "No groups defined."
    return "\n".join(groups)


def cmd_group_show(args: Any) -> str:
    """Show the keys belonging to a group."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    keys = get_group_keys(vault.secrets, args.group)
    if not keys:
        return f"Group '{args.group}' is empty."
    return "\n".join(keys)


def cmd_group_export(args: Any) -> str:
    """Show key=value pairs for every member of a group."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    members = get_group_secrets(vault.secrets, args.group)
    lines = [f"{k}={v}" for k, v in sorted(members.items())]
    return "\n".join(lines)
