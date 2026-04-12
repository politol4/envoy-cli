"""expire_commands.py – CLI command handlers for the expire feature."""
from __future__ import annotations

from envoy_cli.sync import SyncManager
from envoy_cli.expire import find_expired, purge_expired


def _make_manager(args) -> SyncManager:
    return SyncManager(
        vault_dir=getattr(args, "vault_dir", "."),
        passphrase=args.passphrase,
    )


def cmd_expire_list(args) -> str:
    """List all secrets that have expired (dry-run, no deletions)."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.env)
    result = find_expired(vault)
    if not result.has_expired:
        return "No expired secrets."
    lines = ["Expired secrets:"]
    for key in sorted(result.expired):
        lines.append(f"  - {key}")
    return "\n".join(lines)


def cmd_expire_purge(args) -> str:
    """Delete all expired secrets from the vault and persist changes."""
    manager = _make_manager(args)
    vault = manager._load_vault(args.env)
    result = purge_expired(vault)
    if not result.has_expired:
        return "Nothing to purge – no expired secrets found."
    vault_path = manager._vault_path(args.env)
    vault.save(vault_path, args.passphrase)
    return (
        f"Purged {len(result.expired)} expired secret(s): "
        + ", ".join(sorted(result.expired))
    )
