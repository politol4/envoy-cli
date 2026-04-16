"""Switch active environment profile and optionally reload local .env file."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envoy_cli.profile import Profile, ProfileError

_STATE_FILE = ".envoy_active"


class SwitchError(Exception):
    """Raised when an environment switch fails."""


def _state_path(base_dir: str = ".") -> Path:
    return Path(base_dir) / _STATE_FILE


def get_active(base_dir: str = ".") -> Optional[str]:
    """Return the name of the currently active environment, or None."""
    p = _state_path(base_dir)
    if p.exists():
        name = p.read_text().strip()
        return name if name else None
    return None


def set_active(name: str, profiles: dict[str, Profile], base_dir: str = ".") -> str:
    """Persist *name* as the active environment.

    Returns a human-readable confirmation message.
    Raises SwitchError if the profile does not exist.
    """
    if not name:
        raise SwitchError("Environment name must not be empty.")
    if name not in profiles:
        known = ", ".join(sorted(profiles)) or "(none)"
        raise SwitchError(
            f"Unknown environment '{name}'. Known profiles: {known}."
        )
    _state_path(base_dir).write_text(name)
    return f"Switched to environment '{name}'."


def clear_active(base_dir: str = ".") -> str:
    """Remove the active-environment marker."""
    p = _state_path(base_dir)
    if p.exists():
        p.unlink()
        return "Active environment cleared."
    return "No active environment was set."
