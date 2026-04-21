"""CLI command handlers for the bookmark feature."""
from __future__ import annotations

from envoy_cli.bookmark import (
    BookmarkError,
    add_bookmark,
    is_bookmarked,
    list_bookmarks,
    remove_bookmark,
)
from envoy_cli.sync import SyncManager


def _make_manager(args) -> SyncManager:
    return SyncManager(
        env=args.env,
        passphrase=args.passphrase,
        vault_dir=getattr(args, "vault_dir", "."),
    )


def cmd_bookmark_add(args) -> str:
    """Add a bookmark for a secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    note = getattr(args, "note", "") or ""
    try:
        updated = add_bookmark(vault.secrets, args.key, note)
    except BookmarkError as exc:
        raise BookmarkError(str(exc)) from exc
    vault.secrets = updated
    manager._vault_path()
    from envoy_cli.vault import Vault
    vault.save(manager._vault_path(), args.passphrase)
    return f"Bookmarked '{args.key}'."


def cmd_bookmark_remove(args) -> str:
    """Remove a bookmark from a secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        updated = remove_bookmark(vault.secrets, args.key)
    except BookmarkError as exc:
        raise BookmarkError(str(exc)) from exc
    vault.secrets = updated
    vault.save(manager._vault_path(), args.passphrase)
    return f"Bookmark removed for '{args.key}'."


def cmd_bookmark_list(args) -> str:
    """List all bookmarked keys."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    bookmarks = list_bookmarks(vault.secrets)
    if not bookmarks:
        return "No bookmarks found."
    lines = []
    for entry in bookmarks:
        note_part = f"  # {entry['note']}" if entry["note"] else ""
        lines.append(f"  {entry['key']}{note_part}")
    return "Bookmarks:\n" + "\n".join(lines)


def cmd_bookmark_status(args) -> str:
    """Check whether a key is bookmarked."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    if is_bookmarked(vault.secrets, args.key):
        return f"'{args.key}' is bookmarked."
    return f"'{args.key}' is not bookmarked."
