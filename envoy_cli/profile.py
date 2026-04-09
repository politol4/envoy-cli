"""Profile management for envoy-cli.

A profile associates a named environment (e.g. 'staging', 'production')
with a remote base URL and an optional default vault path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

DEFAULT_PROFILES_PATH = Path.home() / ".envoy" / "profiles.json"


class ProfileError(Exception):
    """Raised for profile-related errors."""


class Profile:
    """Represents a single named environment profile."""

    def __init__(self, name: str, base_url: str, vault_path: Optional[str] = None) -> None:
        if not name:
            raise ProfileError("Profile name must not be empty.")
        if not base_url:
            raise ProfileError("Profile base_url must not be empty.")
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.vault_path = vault_path

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "base_url": self.base_url,
            "vault_path": self.vault_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Profile":
        return cls(
            name=str(data["name"]),
            base_url=str(data["base_url"]),
            vault_path=data.get("vault_path"),  # type: ignore[arg-type]
        )


class ProfileStore:
    """Persists and retrieves profiles from a JSON file."""

    def __init__(self, path: Path = DEFAULT_PROFILES_PATH) -> None:
        self.path = path

    def _load_raw(self) -> Dict[str, dict]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_raw(self, data: Dict[str, dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def list(self):
        return [Profile.from_dict(v) for v in self._load_raw().values()]

    def get(self, name: str) -> Profile:
        raw = self._load_raw()
        if name not in raw:
            raise ProfileError(f"Profile '{name}' not found.")
        return Profile.from_dict(raw[name])

    def set(self, profile: Profile) -> None:
        raw = self._load_raw()
        raw[profile.name] = profile.to_dict()
        self._save_raw(raw)

    def delete(self, name: str) -> None:
        raw = self._load_raw()
        if name not in raw:
            raise ProfileError(f"Profile '{name}' not found.")
        del raw[name]
        self._save_raw(raw)
