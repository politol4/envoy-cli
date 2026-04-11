"""Clone all secrets from one environment vault into another."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envoy_cli.sync import SyncManager


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_env(
    manager: "SyncManager",
    src_env: str,
    dst_env: str,
    passphrase: str,
    *,
    overwrite: bool = False,
) -> int:
    """Copy every secret from *src_env* into *dst_env*.

    Parameters
    ----------
    manager:
        A :class:`~envoy_cli.sync.SyncManager` instance used to load/save
        vaults for both environments.
    src_env:
        Name of the source environment (e.g. ``"staging"``).
    dst_env:
        Name of the destination environment (e.g. ``"production"``).
    passphrase:
        Encryption passphrase shared by both vaults.
    overwrite:
        When *False* (default) keys that already exist in *dst_env* are
        preserved.  When *True* they are replaced by the source value.

    Returns
    -------
    int
        Number of secrets written to the destination vault.
    """
    if src_env == dst_env:
        raise CloneError("Source and destination environments must differ.")

    src_vault = manager._load_vault(src_env, passphrase)
    dst_vault = manager._load_vault(dst_env, passphrase)

    src_secrets = src_vault.all()
    if not src_secrets:
        raise CloneError(f"Source environment '{src_env}' contains no secrets.")

    written = 0
    for key, value in src_secrets.items():
        if not overwrite and dst_vault.get(key) is not None:
            continue
        dst_vault.set(key, value)
        written += 1

    manager._save_vault(dst_env, dst_vault, passphrase)
    return written
