"""Search secrets within a vault by key pattern or value pattern."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .vault import Vault


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    matches: Dict[str, str] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.matches)

    @property
    def has_matches(self) -> bool:
        return self.count > 0

    def as_lines(self, reveal_values: bool = False) -> List[str]:
        lines = []
        for key, value in sorted(self.matches.items()):
            display = value if reveal_values else "***"
            lines.append(f"{key}={display}")
        return lines


def search_secrets(
    vault: Vault,
    key_pattern: Optional[str] = None,
    value_pattern: Optional[str] = None,
    use_regex: bool = False,
) -> SearchResult:
    """Search vault secrets by key glob/regex or value glob/regex.

    At least one of *key_pattern* or *value_pattern* must be provided.
    When both are given, a secret must match **both** to be included.

    Args:
        vault: The vault whose secrets are searched.
        key_pattern: A glob (default) or regex pattern matched against keys.
        value_pattern: A glob (default) or regex pattern matched against values.
        use_regex: When True, treat patterns as regular expressions.

    Returns:
        A :class:`SearchResult` containing the matching key/value pairs.

    Raises:
        SearchError: If neither pattern is supplied or a regex is invalid.
    """
    if key_pattern is None and value_pattern is None:
        raise SearchError("At least one of key_pattern or value_pattern must be provided.")

    def _compile(pattern: str) -> re.Pattern:
        try:
            if use_regex:
                return re.compile(pattern)
            return re.compile(fnmatch.translate(pattern), re.IGNORECASE)
        except re.error as exc:
            raise SearchError(f"Invalid pattern {pattern!r}: {exc}") from exc

    key_re = _compile(key_pattern) if key_pattern else None
    val_re = _compile(value_pattern) if value_pattern else None

    matches: Dict[str, str] = {}
    for key, value in vault.all().items():
        if key_re and not key_re.search(key):
            continue
        if val_re and not val_re.search(value):
            continue
        matches[key] = value

    return SearchResult(matches=matches)
