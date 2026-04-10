"""Export vault secrets to various formats (shell, dotenv, JSON, Docker)."""

from __future__ import annotations

import json
import shlex
from typing import Dict, Literal

ExportFormat = Literal["dotenv", "shell", "json", "docker"]

SUPPORTED_FORMATS: tuple[str, ...] = ("dotenv", "shell", "json", "docker")


class ExportError(ValueError):
    """Raised when an unsupported export format is requested."""


def _quote_shell(value: str) -> str:
    """Return a shell-safe quoted value."""
    return shlex.quote(value)


def export_secrets(
    secrets: Dict[str, str],
    fmt: ExportFormat = "dotenv",
) -> str:
    """Render *secrets* as a string in the requested *fmt*.

    Parameters
    ----------
    secrets:
        Mapping of environment variable names to their plaintext values.
    fmt:
        One of ``dotenv``, ``shell``, ``json``, or ``docker``.

    Returns
    -------
    str
        The formatted output ready to be written to a file or stdout.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    if fmt == "dotenv":
        lines = [f'{k}="{v}"' for k, v in sorted(secrets.items())]
        return "\n".join(lines) + ("\n" if lines else "")

    if fmt == "shell":
        lines = [f"export {k}={_quote_shell(v)}" for k, v in sorted(secrets.items())]
        return "\n".join(lines) + ("\n" if lines else "")

    if fmt == "json":
        return json.dumps(dict(sorted(secrets.items())), indent=2) + "\n"

    # docker: --env-file compatible format (KEY=VALUE, no quoting)
    lines = [f"{k}={v}" for k, v in sorted(secrets.items())]
    return "\n".join(lines) + ("\n" if lines else "")
