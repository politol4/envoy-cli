"""Audit log for tracking env variable access and mutations."""

import json
import os
from datetime import datetime, timezone
from typing import List, Optional

AUDIT_LOG_VERSION = 1


class AuditEntry:
    def __init__(self, action: str, key: str, environment: str, user: Optional[str] = None):
        self.action = action          # 'set', 'get', 'delete', 'push', 'pull'
        self.key = key
        self.environment = environment
        self.user = user or os.environ.get("USER", "unknown")
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "version": AUDIT_LOG_VERSION,
            "timestamp": self.timestamp,
            "action": self.action,
            "key": self.key,
            "environment": self.environment,
            "user": self.user,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        entry = cls(
            action=data["action"],
            key=data["key"],
            environment=data["environment"],
            user=data.get("user", "unknown"),
        )
        entry.timestamp = data["timestamp"]
        return entry


class AuditLog:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def _load_entries(self) -> List[dict]:
        if not os.path.exists(self.log_path):
            return []
        entries = []
        with open(self.log_path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Malformed audit log entry at {self.log_path}:{lineno}: {exc}"
                    ) from exc
        return entries

    def record(self, action: str, key: str, environment: str, user: Optional[str] = None) -> AuditEntry:
        entry = AuditEntry(action=action, key=key, environment=environment, user=user)
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict()) + "\n")
        return entry

    def history(self, environment: Optional[str] = None, key: Optional[str] = None) -> List[AuditEntry]:
        entries = [AuditEntry.from_dict(d) for d in self._load_entries()]
        if environment:
            entries = [e for e in entries if e.environment == environment]
        if key:
            entries = [e for e in entries if e.key == key]
        return entries

    def clear(self) -> None:
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
