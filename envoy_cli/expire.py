"""expire.py – bulk expiry report and purge for secrets with TTL metadata."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

from envoy_cli.vault import Vault

_META_PREFIX = "__ttl__"


class ExpireError(Exception):
    pass


@dataclass
class ExpireResult:
    expired: List[str] = field(default_factory=list)
    retained: List[str] = field(default_factory=list)

    @property
    def has_expired(self) -> bool:
        return bool(self.expired)

    def summary(self) -> str:
        if not self.has_expired:
            return "No expired secrets found."
        keys = ", ".join(sorted(self.expired))
        return f"{len(self.expired)} expired secret(s): {keys}"


def find_expired(vault: Vault) -> ExpireResult:
    """Return an ExpireResult listing which secrets have passed their TTL."""
    secrets = vault.all()
    now = time.time()
    result = ExpireResult()

    for key, value in secrets.items():
        if key.startswith(_META_PREFIX):
            continue
        meta_key = f"{_META_PREFIX}{key}"
        ttl_raw = secrets.get(meta_key)
        if ttl_raw is None:
            result.retained.append(key)
            continue
        try:
            expiry = float(ttl_raw)
        except ValueError:
            result.retained.append(key)
            continue
        if expiry <= now:
            result.expired.append(key)
        else:
            result.retained.append(key)

    return result


def purge_expired(vault: Vault) -> ExpireResult:
    """Delete all secrets (and their TTL metadata) that have expired."""
    result = find_expired(vault)
    for key in result.expired:
        meta_key = f"{_META_PREFIX}{key}"
        vault.delete(key)
        try:
            vault.delete(meta_key)
        except Exception:
            pass
    return result
