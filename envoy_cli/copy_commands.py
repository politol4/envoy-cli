"""copy_commands.py – CLI handlers for the copy/move feature."""

from __future__ import annotations

import argparse

from envoy_cli.copy import CopyError, copy_key
from envoy_cli.sync import SyncManager


def _make_manager(args: argparse.Namespace) -> SyncManager:
    return SyncManager(
        env=args.env,
        passphrase=args.passphrase,
        base_url=getattr(args, "base_url", ""),
        token=getattr(args, "token", ""),
    )


def cmd_copy(args: argparse.Namespace) -> str:
    """Handle ``envoy copy <src> <dst>``."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        result = copy_key(
            vault,
            args.src_key,
            args.dst_key,
            overwrite=getattr(args, "overwrite", False),
            move=False,
        )
    except CopyError as exc:
        return f"Error: {exc}"
    manager._save_vault(vault)
    return (
        f"Key '{result['src']}' {result['action']} to '{result['dst']}' "
        f"in environment '{args.env}'."
    )


def cmd_move(args: argparse.Namespace) -> str:
    """Handle ``envoy move <src> <dst>``."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    try:
        result = copy_key(
            vault,
            args.src_key,
            args.dst_key,
            overwrite=getattr(args, "overwrite", False),
            move=True,
        )
    except CopyError as exc:
        return f"Error: {exc}"
    manager._save_vault(vault)
    return (
        f"Key '{result['src']}' {result['action']} to '{result['dst']}' "
        f"in environment '{args.env}'."
    )
