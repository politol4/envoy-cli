"""CLI command handlers for the ``import`` sub-command."""

from __future__ import annotations

import argparse
from typing import Optional

from envoy_cli.import_secrets import ImportError as ImportErr
from envoy_cli.import_secrets import import_from_file, import_secrets
from envoy_cli.sync import SyncManager


def cmd_import_file(
    args: argparse.Namespace,
    manager: Optional[SyncManager] = None,
) -> str:
    """Import secrets from a file into the local vault.

    Expected *args* attributes:
        - ``profile``  (str)  active profile name
        - ``file``     (str)  path to source file
        - ``fmt``      (str | None)  force format override
        - ``prefix``   (str | None)  key prefix filter
        - ``no_overwrite`` (bool)  preserve existing keys
    """
    if manager is None:  # pragma: no cover
        manager = SyncManager(args.profile)

    try:
        existing = manager.get_all()
        merged = import_from_file(
            args.file,
            fmt=args.fmt or None,
            prefix_filter=args.prefix or None,
            overwrite=not args.no_overwrite,
            existing=existing,
        )
    except ImportErr as exc:
        raise SystemExit(f"Import failed: {exc}") from exc

    added = [k for k in merged if k not in existing]
    updated = [k for k in merged if k in existing and merged[k] != existing[k]]

    for key, value in merged.items():
        manager.set(key, value)

    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if updated:
        parts.append(f"{len(updated)} updated")
    if not parts:
        return "Nothing changed."
    return "Imported: " + ", ".join(parts) + "."


def cmd_import_stdin(
    args: argparse.Namespace,
    manager: Optional[SyncManager] = None,
    stdin_text: str = "",
) -> str:
    """Import secrets from stdin into the local vault."""
    if manager is None:  # pragma: no cover
        manager = SyncManager(args.profile)

    try:
        existing = manager.get_all()
        merged = import_secrets(
            stdin_text,
            fmt=args.fmt or "dotenv",
            prefix_filter=args.prefix or None,
            overwrite=not args.no_overwrite,
            existing=existing,
        )
    except ImportErr as exc:
        raise SystemExit(f"Import failed: {exc}") from exc

    added = [k for k in merged if k not in existing]
    updated = [k for k in merged if k in existing and merged[k] != existing[k]]

    for key, value in merged.items():
        manager.set(key, value)

    parts = []
    if added:
        parts.append(f"{len(added)} added")
    if updated:
        parts.append(f"{len(updated)} updated")
    if not parts:
        return "Nothing changed."
    return "Imported: " + ", ".join(parts) + "."
