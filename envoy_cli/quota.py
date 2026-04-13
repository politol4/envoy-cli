"""Quota management: enforce max secret count per environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

DEFAULT_QUOTA = 500
_META_KEY = "__quota__"


class QuotaError(Exception):
    """Raised when a quota operation fails."""


@dataclass
class QuotaConfig:
    limit: int
    env: str

    def to_dict(self) -> Dict:
        return {"limit": self.limit, "env": self.env}

    @classmethod
    def from_dict(cls, data: Dict) -> "QuotaConfig":
        for key in ("limit", "env"):
            if key not in data:
                raise QuotaError(f"Missing field: {key}")
        return cls(limit=int(data["limit"]), env=str(data["env"]))


def set_quota(secrets: Dict[str, str], limit: int, env: str) -> Dict[str, str]:
    """Store a quota limit for the given environment."""
    if limit < 1:
        raise QuotaError("Quota limit must be a positive integer.")
    updated = dict(secrets)
    config = QuotaConfig(limit=limit, env=env)
    import json
    updated[_META_KEY] = json.dumps(config.to_dict())
    return updated


def get_quota(secrets: Dict[str, str], env: str) -> Optional[QuotaConfig]:
    """Return the QuotaConfig for env, or None if not set."""
    import json
    raw = secrets.get(_META_KEY)
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if data.get("env") != env:
        return None
    return QuotaConfig.from_dict(data)


def check_quota(secrets: Dict[str, str], env: str, adding: int = 1) -> None:
    """Raise QuotaError if adding `adding` secrets would exceed the quota."""
    config = get_quota(secrets, env)
    limit = config.limit if config else DEFAULT_QUOTA
    # exclude meta keys from count
    current = sum(1 for k in secrets if not k.startswith("__"))
    if current + adding > limit:
        raise QuotaError(
            f"Quota exceeded for env '{env}': limit is {limit}, "
            f"current count is {current}, tried to add {adding}."
        )


def remove_quota(secrets: Dict[str, str]) -> Dict[str, str]:
    """Remove the quota meta key from secrets."""
    updated = dict(secrets)
    updated.pop(_META_KEY, None)
    return updated
