"""CLI command handlers for the mask feature."""

from __future__ import annotations

import argparse
from typing import Any

from envoy_cli.mask import mask_secrets, reveal_preview, MaskError
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


def _make_manager(args: argparse.Namespace) -> SyncManager:
    profile = getattr(args, "profile", "default")
    return SyncManager(profile)


def cmd_mask_show(args: argparse.Namespace) -> str:
    """Print all secrets with values masked."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    secrets = vault.all()
    if not secrets:
        return "No secrets found."
    masked = mask_secrets(secrets)
    lines = [f"{k}={v}" for k, v in sorted(masked.items())]
    return "\n".join(lines)


def cmd_mask_peek(args: argparse.Namespace) -> str:
    """Show a masked preview of a single secret key."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.passphrase)
    value = vault.get(args.key)
    if value is None:
        raise MaskError(f"Key not found: {args.key!r}")
    preview = reveal_preview(value, visible=getattr(args, "visible", 4))
    return f"{args.key}={preview}"
