"""CLI command handlers for batch set / batch delete."""

from __future__ import annotations

import json
from argparse import Namespace
from typing import List

from envoy_cli.batch import BatchError, batch_delete, batch_set
from envoy_cli.sync import SyncManager


def _make_manager(args: Namespace) -> SyncManager:
    return SyncManager(base_dir=getattr(args, "vault_dir", "."))


def cmd_batch_set(args: Namespace) -> str:
    """Handle `envoy batch-set KEY=VALUE ...`.

    Expects args.pairs as a list of 'KEY=VALUE' strings,
    args.env, args.passphrase, and optional args.no_overwrite.
    """
    manager = _make_manager(args)
    pairs: dict = {}
    for item in args.pairs:
        if "=" not in item:
            raise BatchError(f"invalid pair (expected KEY=VALUE): {item!r}")
        key, _, value = item.partition("=")
        pairs[key.strip()] = value

    overwrite = not getattr(args, "no_overwrite", False)
    applied, skipped = batch_set(
        manager, args.env, args.passphrase, pairs, overwrite=overwrite
    )

    parts: List[str] = []
    if applied:
        parts.append(f"Set {len(applied)} key(s): {', '.join(sorted(applied))}")
    if skipped:
        parts.append(f"Skipped {len(skipped)} existing key(s): {', '.join(sorted(skipped))}")
    return "\n".join(parts) if parts else "Nothing to do."


def cmd_batch_delete(args: Namespace) -> str:
    """Handle `envoy batch-delete KEY ...`.

    Expects args.keys as a list of key names,
    args.env, args.passphrase, and optional args.ignore_missing.
    """
    manager = _make_manager(args)
    ignore_missing = getattr(args, "ignore_missing", False)

    deleted, missing = batch_delete(
        manager, args.env, args.passphrase, args.keys,
        ignore_missing=ignore_missing,
    )

    parts: List[str] = []
    if deleted:
        parts.append(f"Deleted {len(deleted)} key(s): {', '.join(sorted(deleted))}")
    if missing:
        parts.append(f"Missing (skipped) {len(missing)} key(s): {', '.join(sorted(missing))}")
    return "\n".join(parts) if parts else "Nothing to do."
