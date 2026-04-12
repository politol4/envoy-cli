"""Mask secrets for safe display in logs and CLI output."""

from __future__ import annotations

from typing import Dict, List


class MaskError(Exception):
    """Raised when masking operations fail."""


_MASK_CHAR = "*"
_DEFAULT_VISIBLE = 4
_MIN_LENGTH_TO_PARTIAL = 8


def mask_value(value: str, visible: int = _DEFAULT_VISIBLE) -> str:
    """Return a masked version of *value*.

    If the value is shorter than *_MIN_LENGTH_TO_PARTIAL* characters the
    entire string is replaced with asterisks so that the length itself does
    not leak information.
    """
    if not isinstance(value, str):
        raise MaskError(f"Expected str, got {type(value).__name__}")
    if len(value) < _MIN_LENGTH_TO_PARTIAL:
        return _MASK_CHAR * max(len(value), 4)
    shown = value[:visible]
    return shown + _MASK_CHAR * (len(value) - visible)


def mask_secrets(
    secrets: Dict[str, str],
    *,
    visible: int = _DEFAULT_VISIBLE,
    skip_keys: List[str] | None = None,
) -> Dict[str, str]:
    """Return a new dict with all values masked.

    Keys listed in *skip_keys* are passed through unchanged (useful for
    non-sensitive metadata keys such as __tags__ or __ttl__).
    """
    skip = set(skip_keys or [])
    result: Dict[str, str] = {}
    for key, value in secrets.items():
        if key in skip or key.startswith("__"):
            result[key] = value
        else:
            result[key] = mask_value(value, visible=visible)
    return result


def reveal_preview(value: str, visible: int = _DEFAULT_VISIBLE) -> str:
    """Return a short preview string suitable for CLI hints.

    Example: ``ABCD****`` (4 chars shown, rest masked).
    """
    masked = mask_value(value, visible=visible)
    return masked
