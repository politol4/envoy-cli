"""CLI command handlers for the archive feature."""

from __future__ import annotations

import os
from argparse import Namespace
from typing import Callable

from envoy_cli.archive import (
    ArchiveError,
    archive_key,
    list_archived,
    purge_archived,
    unarchive_key,
)
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


def _make_manager(args: Namespace) -> SyncManager:
    passphrase = os.environ.get("ENVOY_PASSPHRASE", "")
    return SyncManager(env=args.env, passphrase=passphrase)


def cmd_archive_key(args: Namespace) -> str:
    """Archive a single secret key."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    secrets = vault.all()
    try:
        updated = archive_key(secrets, args.key)
    except ArchiveError as exc:
        raise ArchiveError(str(exc)) from exc
    new_vault = Vault(passphrase=mgr._passphrase)
    new_vault._secrets = updated
    mgr._save_vault(new_vault)
    return f"Key '{args.key}' archived in '{args.env}'."


def cmd_unarchive_key(args: Namespace) -> str:
    """Restore an archived key to the live namespace."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    secrets = vault.all()
    try:
        updated = unarchive_key(secrets, args.key)
    except ArchiveError as exc:
        raise ArchiveError(str(exc)) from exc
    new_vault = Vault(passphrase=mgr._passphrase)
    new_vault._secrets = updated
    mgr._save_vault(new_vault)
    return f"Key '{args.key}' restored in '{args.env}'."


def cmd_archive_list(args: Namespace) -> str:
    """List all archived keys."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    keys = list_archived(vault.all())
    if not keys:
        return f"No archived keys in '{args.env}'."
    return "\n".join(keys)


def cmd_archive_purge(args: Namespace) -> str:
    """Permanently delete all archived keys."""
    mgr = _make_manager(args)
    vault = mgr._load_vault()
    secrets = vault.all()
    updated = purge_archived(secrets)
    removed = len(secrets) - len(updated)
    new_vault = Vault(passphrase=mgr._passphrase)
    new_vault._secrets = updated
    mgr._save_vault(new_vault)
    return f"Purged {removed} archived key(s) from '{args.env}'."
