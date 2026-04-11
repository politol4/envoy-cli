"""Secret change history tracking for envoy-cli."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional


class HistoryError(Exception):
    """Raised when a history operation fails."""


@dataclass
class HistoryEntry:
    action: str          # 'set', 'delete', 'rotate'
    key: str
    env: str
    timestamp: float = field(default_factory=time.time)
    actor: str = "local"
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "key": self.key,
            "env": self.env,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        required = {"action", "key", "env", "timestamp"}
        missing = required - data.keys()
        if missing:
            raise HistoryError(f"Missing fields in history entry: {missing}")
        return cls(
            action=data["action"],
            key=data["key"],
            env=data["env"],
            timestamp=data["timestamp"],
            actor=data.get("actor", "local"),
            note=data.get("note", ""),
        )


class History:
    """Append-only history log stored as newline-delimited JSON."""

    def __init__(self, path: str) -> None:
        self._path = path

    def record(self, entry: HistoryEntry) -> None:
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")

    def entries(self, env: Optional[str] = None, key: Optional[str] = None) -> List[HistoryEntry]:
        if not os.path.exists(self._path):
            return []
        results: List[HistoryEntry] = []
        with open(self._path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                entry = HistoryEntry.from_dict(json.loads(line))
                if env and entry.env != env:
                    continue
                if key and entry.key != key:
                    continue
                results.append(entry)
        return results

    def clear(self) -> int:
        if not os.path.exists(self._path):
            return 0
        count = len(self.entries())
        os.remove(self._path)
        return count
