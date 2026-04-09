"""Utilities for parsing and serializing .env files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional

# Matches: KEY=VALUE, KEY="VALUE", KEY='VALUE', with optional export prefix
_LINE_RE = re.compile(
    r'^(?:export\s+)?'
    r'([A-Za-z_][A-Za-z0-9_]*)'
    r'\s*=\s*'
    r'("(?:[^"\\]|\\.)*"|\x27(?:[^\x27\\]|\\.)*\x27|[^#\r\n]*)'
    r'(?:\s*#.*)?$'
)


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]
    return value


def parse(text: str) -> Dict[str, str]:
    """Parse .env file content into a key/value dictionary.

    - Blank lines and comment lines (starting with #) are ignored.
    - Values may be quoted with single or double quotes.
    - Inline comments after unquoted values are stripped.
    """
    result: Dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        match = _LINE_RE.match(stripped)
        if match:
            key, raw_value = match.group(1), match.group(2)
            result[key] = _strip_quotes(raw_value)
    return result


def serialize(env: Dict[str, str]) -> str:
    """Serialize a key/value dictionary back to .env file content.

    Values containing spaces or special characters are double-quoted.
    """
    lines = []
    for key, value in env.items():
        if not value or re.search(r'[\s"\x27#\\]', value):
            escaped = value.replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f'{key}={value}')
    return '\n'.join(lines) + ('\n' if lines else '')


def load_file(path: str | Path) -> Dict[str, str]:
    """Read and parse a .env file from disk."""
    content = Path(path).read_text(encoding='utf-8')
    return parse(content)


def save_file(path: str | Path, env: Dict[str, str]) -> None:
    """Serialize and write a dictionary to a .env file on disk."""
    Path(path).write_text(serialize(env), encoding='utf-8')
