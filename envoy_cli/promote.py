"""Promote secrets from one environment to another with optional key filtering."""

from __future__ import annotations

from typing import Dict, List, Optional

from .sync import SyncManager


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


class PromoteResult:
    def __init__(
        self,
        src_env: str,
        dst_env: str,
        promoted: List[str],
        skipped: List[str],
    ) -> None:
        self.src_env = src_env
        self.dst_env = dst_env
        self.promoted = promoted
        self.skipped = skipped

    @property
    def has_changes(self) -> bool:
        return len(self.promoted) > 0

    def summary(self) -> str:
        lines = [
            f"Promote {self.src_env} -> {self.dst_env}",
            f"  promoted : {len(self.promoted)}",
            f"  skipped  : {len(self.skipped)}",
        ]
        return "\n".join(lines)


def promote_env(
    manager: SyncManager,
    src_env: str,
    dst_env: str,
    passphrase: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
) -> PromoteResult:
    """Copy secrets from *src_env* into *dst_env*.

    Parameters
    ----------
    manager:    SyncManager used to load / save vaults.
    src_env:    Source environment name (e.g. ``"staging"``).
    dst_env:    Destination environment name (e.g. ``"production"``).
    passphrase: Encryption passphrase shared by both vaults.
    keys:       Optional allowlist of secret keys to promote.  When *None*
                every non-meta key is promoted.
    overwrite:  When *False*, keys that already exist in *dst_env* are
                skipped rather than overwritten.
    """
    if src_env == dst_env:
        raise PromoteError("Source and destination environments must differ.")

    src_vault = manager._load_vault(src_env, passphrase)
    dst_vault = manager._load_vault(dst_env, passphrase)

    src_secrets: Dict[str, str] = src_vault.all()

    candidate_keys = list(keys) if keys is not None else list(src_secrets.keys())

    # Validate requested keys exist in source
    missing = [k for k in candidate_keys if k not in src_secrets]
    if missing:
        raise PromoteError(
            f"Keys not found in '{src_env}': {', '.join(sorted(missing))}"
        )

    promoted: List[str] = []
    skipped: List[str] = []

    for key in candidate_keys:
        if not overwrite and dst_vault.get(key) is not None:
            skipped.append(key)
            continue
        dst_vault.set(key, src_secrets[key])
        promoted.append(key)

    manager._save_vault(dst_env, dst_vault, passphrase)

    return PromoteResult(
        src_env=src_env,
        dst_env=dst_env,
        promoted=sorted(promoted),
        skipped=sorted(skipped),
    )
