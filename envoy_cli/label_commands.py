"""CLI command handlers for label management."""

from __future__ import annotations

import os
from argparse import Namespace
from typing import Callable

from envoy_cli.label import LabelError, add_label, get_labels, list_labeled, remove_label
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


def _make_manager(args: Namespace) -> SyncManager:
    env = getattr(args, "env", "default")
    passphrase = os.environ.get("ENVOY_PASSPHRASE", "")
    return SyncManager(env=env, passphrase=passphrase)


def cmd_label_add(args: Namespace) -> str:
    """Add a label to a secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = add_label(vault.secrets, args.key, args.label)
    except LabelError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Label '{args.label}' added to '{args.key}'."


def cmd_label_remove(args: Namespace) -> str:
    """Remove a label from a secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        vault.secrets = remove_label(vault.secrets, args.key, args.label)
    except LabelError as exc:
        raise SystemExit(str(exc)) from exc
    manager._save_vault(vault)
    return f"Label '{args.label}' removed from '{args.key}'."


def cmd_label_list(args: Namespace) -> str:
    """List all labels on a secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        labels = get_labels(vault.secrets, args.key)
    except LabelError as exc:
        raise SystemExit(str(exc)) from exc
    if not labels:
        return f"No labels set on '{args.key}'."
    return "\n".join(labels)


def cmd_label_find(args: Namespace) -> str:
    """Find all keys that carry a given label."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    keys = list_labeled(vault.secrets, args.label)
    if not keys:
        return f"No keys found with label '{args.label}'."
    return "\n".join(keys)
