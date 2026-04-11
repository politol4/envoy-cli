"""copy.py – copy or move a secret key within or across environments."""

from __future__ import annotations

from typing import Dict

from envoy_cli.vault import Vault


class CopyError(Exception):
    """Raised when a copy/move operation cannot be completed."""


def copy_key(
    vault: Vault,
    src_key: str,
    dst_key: str,
    *,
    overwrite: bool = False,
    move: bool = False,
) -> Dict[str, str]:
    """Copy *src_key* to *dst_key* inside *vault*.

    Parameters
    ----------
    vault:     The vault to operate on.
    src_key:   Existing key to copy.
    dst_key:   Destination key name.
    overwrite: Allow overwriting an existing destination key.
    move:      If True, delete *src_key* after copying (rename semantics).

    Returns
    -------
    A dict with ``src``, ``dst``, and ``action`` (``'copied'`` or ``'moved'``).
    """
    if not src_key:
        raise CopyError("src_key must not be empty.")
    if not dst_key:
        raise CopyError("dst_key must not be empty.")
    if src_key == dst_key:
        raise CopyError("src_key and dst_key must be different.")

    secrets = vault.all()

    if src_key not in secrets:
        raise CopyError(f"Key '{src_key}' does not exist in the vault.")
    if dst_key in secrets and not overwrite:
        raise CopyError(
            f"Key '{dst_key}' already exists. Pass overwrite=True to replace it."
        )

    vault.set(dst_key, secrets[src_key])
    if move:
        vault.delete(src_key)
        action = "moved"
    else:
        action = "copied"

    return {"src": src_key, "dst": dst_key, "action": action}
