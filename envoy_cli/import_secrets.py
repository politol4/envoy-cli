"""Import secrets from external sources (.env files, JSON, shell exports)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envoy_cli.env_file import parse


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


SUPPORTED_FORMATS = ("dotenv", "json")


def _load_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env-style text block into key/value pairs."""
    return parse(text)


def _load_json(text: str) -> Dict[str, str]:
    """Parse a JSON object into key/value pairs (values coerced to str)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    return {str(k): str(v) for k, v in data.items()}


def import_secrets(
    source: str,
    fmt: str = "dotenv",
    *,
    prefix_filter: Optional[str] = None,
    overwrite: bool = True,
    existing: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Import secrets from *source* text.

    Args:
        source:        Raw text content to import.
        fmt:           One of ``"dotenv"`` or ``"json"``.
        prefix_filter: If set, only keys starting with this prefix are imported.
        overwrite:     When *False*, existing keys in *existing* are preserved.
        existing:      Current secrets dict to merge into.

    Returns:
        Merged secrets dict.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ImportError(f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}")

    loaders = {"dotenv": _load_dotenv, "json": _load_json}
    incoming = loaders[fmt](source)

    if not incoming:
        raise ImportError("Source contains no key/value pairs.")

    if prefix_filter:
        incoming = {k: v for k, v in incoming.items() if k.startswith(prefix_filter)}
        if not incoming:
            raise ImportError(f"No keys found with prefix '{prefix_filter}'.")

    base = dict(existing) if existing else {}
    for key, value in incoming.items():
        if overwrite or key not in base:
            base[key] = value
    return base


def import_from_file(
    path: str,
    fmt: Optional[str] = None,
    **kwargs,
) -> Dict[str, str]:
    """Convenience wrapper that reads *path* and delegates to :func:`import_secrets`."""
    p = Path(path)
    if not p.exists():
        raise ImportError(f"File not found: {path}")
    if fmt is None:
        fmt = "json" if p.suffix.lower() == ".json" else "dotenv"
    return import_secrets(p.read_text(encoding="utf-8"), fmt=fmt, **kwargs)
