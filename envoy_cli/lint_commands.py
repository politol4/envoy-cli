"""CLI command handlers for the lint feature."""
from __future__ import annotations

import argparse
import os

from envoy_cli.lint import LintError, lint_vault
from envoy_cli.sync import SyncManager


def _make_manager(args: argparse.Namespace) -> SyncManager:
    passphrase = os.environ.get("ENVOY_PASSPHRASE", "")
    return SyncManager(
        env=args.env,
        passphrase=passphrase,
        base_url=getattr(args, "base_url", ""),
        api_key=getattr(args, "api_key", ""),
    )


def cmd_lint(args: argparse.Namespace) -> str:
    """Run lint checks on the local vault for *args.env*.

    Returns a human-readable report string.
    Raises LintError if the vault cannot be loaded.
    """
    manager = _make_manager(args)
    try:
        vault = manager._load_vault()
    except Exception as exc:  # noqa: BLE001
        raise LintError(f"Could not load vault for env '{args.env}': {exc}") from exc

    report = lint_vault(vault)
    return report.summary()
