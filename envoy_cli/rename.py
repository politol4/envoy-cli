"""Rename a secret key within a vault, preserving its value and tags."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from envoy_cli.vault import Vault


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_key(vault: "Vault", old_key: str, new_key: str) -> None:
    """Rename *old_key* to *new_key* inside *vault*.

    Rules
    -----
    - *old_key* must exist.
    - *new_key* must not already exist (to avoid silent overwrites).
    - Any ``__tags__.<old_key>`` metadata entry is migrated to
      ``__tags__.<new_key>`` automatically.
    - The vault is **not** saved to disk; the caller is responsible for
      persisting the change (mirrors the pattern used in ``tag.py``).

    Raises
    ------
    RenameError
        If *old_key* is missing, *new_key* already exists, or either key
        name is empty.
    """
    if not old_key or not old_key.strip():
        raise RenameError("old_key must not be empty.")
    if not new_key or not new_key.strip():
        raise RenameError("new_key must not be empty.")

    old_key = old_key.strip()
    new_key = new_key.strip()

    secrets: dict[str, str] = vault.all()

    if old_key not in secrets:
        raise RenameError(f"Key '{old_key}' does not exist in the vault.")
    if new_key in secrets:
        raise RenameError(
            f"Key '{new_key}' already exists. Delete it first or choose a "
            "different name."
        )

    value = vault.get(old_key)
    vault.set(new_key, value)
    vault.delete(old_key)

    # Migrate tag metadata if present.
    old_tag_key = f"__tags__.{old_key}"
    new_tag_key = f"__tags__.{new_key}"
    try:
        tag_value = vault.get(old_tag_key)
        vault.set(new_tag_key, tag_value)
        vault.delete(old_tag_key)
    except KeyError:
        pass  # No tags for this key — nothing to migrate.
