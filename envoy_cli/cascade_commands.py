"""CLI command handlers for the cascade feature."""

from __future__ import annotations

import os
from argparse import Namespace
from typing import Optional

from .cascade import CascadeError, cascade
from .sync import SyncManager
from .vault import Vault


def _make_manager(args: Namespace) -> SyncManager:
    profile = getattr(args, "profile", "default")
    return SyncManager(profile)


def _load_vault(path: str, passphrase: str) -> Vault:
    v = Vault(path)
    v.load(passphrase)
    return v


def cmd_cascade(
    args: Namespace,
    *,
    source_vault: Optional[Vault] = None,
    target_vault: Optional[Vault] = None,
) -> str:
    """Cascade missing secrets from a source vault file into the target environment.

    Expected args attributes:
        source_file  – path to the source .vault file
        source_passphrase – passphrase for the source vault
        target_file  – path to the target .vault file
        target_passphrase – passphrase for the target vault
        prefix       – (optional) only cascade keys starting with this prefix
    """
    prefix: str = getattr(args, "prefix", "") or ""

    if source_vault is None:
        if not os.path.isfile(args.source_file):
            raise CascadeError(f"source file not found: {args.source_file}")
        source_vault = _load_vault(args.source_file, args.source_passphrase)

    if target_vault is None:
        if not os.path.isfile(args.target_file):
            raise CascadeError(f"target file not found: {args.target_file}")
        target_vault = _load_vault(args.target_file, args.target_passphrase)

    source_secrets = source_vault.all()
    result = cascade(source_secrets, target_vault, args.target_passphrase, prefix=prefix)

    if result.has_changes:
        target_vault.save(args.target_passphrase)

    lines = [f"Cascade complete: {result.summary()}"]
    lines.extend(result.as_lines())
    return "\n".join(lines)
