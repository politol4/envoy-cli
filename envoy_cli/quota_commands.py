"""CLI command handlers for quota management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envoy_cli.sync import SyncManager
from envoy_cli.quota import (
    QuotaError,
    set_quota,
    get_quota,
    remove_quota,
    DEFAULT_QUOTA,
)


def _make_manager(args: argparse.Namespace) -> SyncManager:
    vault_dir = getattr(args, "vault_dir", ".envoy")
    passphrase = getattr(args, "passphrase", "")
    env = getattr(args, "env", "local")
    return SyncManager(vault_dir=vault_dir, passphrase=passphrase, env=env)


def cmd_quota_set(args: argparse.Namespace) -> str:
    """Set a quota limit for the current environment."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    secrets = vault.all()
    try:
        updated = set_quota(secrets, limit=args.limit, env=args.env)
    except QuotaError as exc:
        raise QuotaError(str(exc)) from exc
    vault._secrets = updated
    manager._vault_path(args.env)  # ensure path exists
    vault.save(str(manager._vault_path(args.env)))
    return f"Quota set to {args.limit} secrets for env '{args.env}'."


def cmd_quota_get(args: argparse.Namespace) -> str:
    """Show the current quota limit for the environment."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    secrets = vault.all()
    config = get_quota(secrets, env=args.env)
    if config is None:
        return (
            f"No quota configured for env '{args.env}'. "
            f"Default limit is {DEFAULT_QUOTA}."
        )
    return f"Quota for env '{args.env}': {config.limit} secrets."


def cmd_quota_remove(args: argparse.Namespace) -> str:
    """Remove the quota limit for the current environment."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    secrets = vault.all()
    updated = remove_quota(secrets)
    vault._secrets = updated
    vault.save(str(manager._vault_path(args.env)))
    return f"Quota removed for env '{args.env}'."


def cmd_quota_check(args: argparse.Namespace) -> str:
    """Report how many secrets are used vs the quota."""
    manager = _make_manager(args)
    vault = manager._load_vault()
    secrets = vault.all()
    config = get_quota(secrets, env=args.env)
    limit = config.limit if config else DEFAULT_QUOTA
    count = sum(1 for k in secrets if not k.startswith("__"))
    remaining = limit - count
    status = "OK" if remaining >= 0 else "EXCEEDED"
    return (
        f"Env '{args.env}': {count}/{limit} secrets used, "
        f"{max(remaining, 0)} remaining. [{status}]"
    )
