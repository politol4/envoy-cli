"""High-level commands for profile management used by the CLI."""

from __future__ import annotations

from typing import List, Optional

from .profile import Profile, ProfileError, ProfileStore


def cmd_profile_add(
    store: ProfileStore,
    name: str,
    base_url: str,
    vault_path: Optional[str] = None,
) -> str:
    """Add or update a profile. Returns a human-readable status message."""
    profile = Profile(name=name, base_url=base_url, vault_path=vault_path)
    existing_names = {p.name for p in store.list()}
    store.set(profile)
    verb = "Updated" if name in existing_names else "Added"
    return f"{verb} profile '{name}' -> {profile.base_url}"


def cmd_profile_list(store: ProfileStore) -> List[str]:
    """Return formatted lines describing all profiles."""
    profiles = store.list()
    if not profiles:
        return ["No profiles configured. Use 'envoy profile add' to create one."]
    lines: List[str] = []
    for p in sorted(profiles, key=lambda x: x.name):
        vault_info = f"  vault: {p.vault_path}" if p.vault_path else ""
        lines.append(f"  {p.name:<20} {p.base_url}{vault_info}")
    return lines


def cmd_profile_remove(store: ProfileStore, name: str) -> str:
    """Remove a profile by name. Returns a status message."""
    store.delete(name)  # raises ProfileError if not found
    return f"Removed profile '{name}'."


def cmd_profile_show(store: ProfileStore, name: str) -> List[str]:
    """Return formatted detail lines for a single profile."""
    p = store.get(name)  # raises ProfileError if not found
    lines = [
        f"Name:       {p.name}",
        f"Base URL:   {p.base_url}",
        f"Vault Path: {p.vault_path or '(default)'}",
    ]
    return lines
