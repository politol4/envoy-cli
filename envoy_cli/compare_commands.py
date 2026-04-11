"""CLI command handlers for the compare feature."""

from __future__ import annotations

import argparse
import os
from typing import Optional

from envoy_cli.compare import CompareError, compare_vaults
from envoy_cli.sync import SyncManager
from envoy_cli.vault import Vault


def _load_local_vault(env: str, passphrase: str, vault_dir: str) -> Vault:
    """Load a vault from the local filesystem for the given env name."""
    manager = SyncManager(
        env=env,
        passphrase=passphrase,
        vault_dir=vault_dir,
        client=None,  # type: ignore[arg-type]
    )
    return manager._load_vault()


def cmd_compare(
    args: argparse.Namespace,
    vault_dir: str = ".",
) -> str:
    """
    Compare two local environment vaults.

    Expected args attributes:
        env_a (str): first environment name
        env_b (str): second environment name
        passphrase (str): shared passphrase for both vaults
        prefix (str | None): optional key prefix filter
    """
    passphrase: str = args.passphrase
    env_a: str = args.env_a
    env_b: str = args.env_b
    prefix: Optional[str] = getattr(args, "prefix", None)

    try:
        vault_a = _load_local_vault(env_a, passphrase, vault_dir)
        vault_b = _load_local_vault(env_b, passphrase, vault_dir)
    except Exception as exc:
        raise CompareError(f"Failed to load vaults: {exc}") from exc

    report = compare_vaults(vault_a, vault_b, env_a=env_a, env_b=env_b, prefix=prefix)
    return report.summary()
