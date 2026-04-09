"""Key rotation: re-encrypt vault contents under a new passphrase."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .vault import Vault

if TYPE_CHECKING:
    from pathlib import Path


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    vault_path: "Path | str",
    old_passphrase: str,
    new_passphrase: str,
) -> int:
    """Re-encrypt *vault_path* under *new_passphrase*.

    Opens the vault with *old_passphrase*, decrypts every stored secret,
    then re-encrypts and saves them all under *new_passphrase*.

    Returns the number of secrets that were rotated.

    Raises
    ------
    RotationError
        If *old_passphrase* is identical to *new_passphrase*, or if the
        vault cannot be opened with *old_passphrase*.
    """
    if old_passphrase == new_passphrase:
        raise RotationError("New passphrase must differ from the current one.")

    try:
        old_vault = Vault(str(vault_path), old_passphrase)
        old_vault.load()
    except Exception as exc:
        raise RotationError(f"Failed to open vault with old passphrase: {exc}") from exc

    keys = old_vault.list()
    if not keys:
        return 0

    new_vault = Vault(str(vault_path), new_passphrase)
    # Do NOT call new_vault.load() — we build fresh state from old plaintext.
    for key in keys:
        plaintext = old_vault.get(key)
        if plaintext is not None:
            new_vault.set(key, plaintext)

    new_vault.save()
    return len(keys)
