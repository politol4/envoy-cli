"""CLI command handlers for namespace operations."""

from __future__ import annotations

from envoy_cli.namespace import (
    NamespaceError,
    keys_in_namespace,
    list_namespaces,
    move_namespace,
    namespace_key,
)
from envoy_cli.sync import SyncManager


def _make_manager(args) -> SyncManager:
    return SyncManager(env=args.env, passphrase=args.passphrase)


def cmd_namespace_list(args) -> str:
    """List all namespaces present in the vault."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    namespaces = list_namespaces(vault.all())
    if not namespaces:
        return "No namespaces found."
    return "\n".join(namespaces)


def cmd_namespace_show(args) -> str:
    """Show all keys (bare names) inside a namespace."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    ns_keys = keys_in_namespace(vault.all(), args.namespace)
    if not ns_keys:
        return f"Namespace '{args.namespace}' is empty or does not exist."
    lines = [f"{k} = {v}" for k, v in sorted(ns_keys.items())]
    return "\n".join(lines)


def cmd_namespace_set(args) -> str:
    """Set a key inside a namespace: envoy namespace set <ns> <key> <value>."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    full_key = namespace_key(args.namespace, args.key)
    vault.set(full_key, args.value)
    vault.save()
    return f"Set '{full_key}' in environment '{args.env}'."


def cmd_namespace_delete(args) -> str:
    """Delete a key inside a namespace."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    full_key = namespace_key(args.namespace, args.key)
    vault.delete(full_key)
    vault.save()
    return f"Deleted '{full_key}' from environment '{args.env}'."


def cmd_namespace_move(args) -> str:
    """Rename all keys from one namespace to another."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    updated = move_namespace(vault.all(), args.src, args.dst)
    # Replace vault contents
    for k in list(vault.all().keys()):
        vault.delete(k)
    for k, v in updated.items():
        vault.set(k, v)
    vault.save()
    count = sum(1 for k in updated if k.startswith(args.dst + "."))
    return f"Moved {count} key(s) from namespace '{args.src}' to '{args.dst}'."
