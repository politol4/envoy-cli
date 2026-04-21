"""Notification dispatch for vault events."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional


class NotifyError(Exception):
    """Raised when a notification cannot be dispatched."""


@dataclass
class NotifyConfig:
    channel: str          # 'slack' | 'email' | 'log'
    target: str           # webhook URL, email address, or file path
    events: List[str] = field(default_factory=list)  # empty = all events
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "channel": self.channel,
            "target": self.target,
            "events": list(self.events),
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NotifyConfig":
        for key in ("channel", "target"):
            if key not in data:
                raise NotifyError(f"Missing required field: {key}")
        return cls(
            channel=data["channel"],
            target=data["target"],
            events=list(data.get("events", [])),
            enabled=bool(data.get("enabled", True)),
        )


SUPPORTED_CHANNELS = frozenset({"slack", "email", "log"})


def _matches_event(config: NotifyConfig, event: str) -> bool:
    """Return True if this config should fire for *event*."""
    return config.enabled and (not config.events or event in config.events)


def _dispatch_log(config: NotifyConfig, payload: dict) -> None:
    """Append a JSON line to a log file."""
    with open(config.target, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")


def _validate_configs(configs: List[NotifyConfig]) -> None:
    """Raise NotifyError if any config contains an unsupported channel.

    Validates all configs up-front so callers discover configuration mistakes
    before any notifications are dispatched.
    """
    for cfg in configs:
        if cfg.channel not in SUPPORTED_CHANNELS:
            raise NotifyError(
                f"Unknown channel '{cfg.channel}'; "
                f"supported channels are: {', '.join(sorted(SUPPORTED_CHANNELS))}"
            )


def dispatch_notification(
    configs: List[NotifyConfig],
    event: str,
    env: str,
    details: Optional[dict] = None,
    *,
    _http_post=None,
) -> int:
    """Fire notifications for *event* across all matching configs.

    Returns the number of notifications dispatched.
    *_http_post* is an injectable callable ``(url, payload) -> None`` used in
    tests to avoid real HTTP calls.
    """
    if not event:
        raise NotifyError("event must not be empty")
    if not env:
        raise NotifyError("env must not be empty")

    _validate_configs(configs)

    payload = {"event": event, "env": env, **(details or {})}
    dispatched = 0

    for cfg in configs:
        if not _matches_event(cfg, event):
            continue
        if cfg.channel == "log":
            _dispatch_log(cfg, payload)
        elif cfg.channel in ("slack", "email"):
            if _http_post is None:
                raise NotifyError(
                    f"HTTP transport required for channel '{cfg.channel}'"
                )
            _http_post(cfg.target, payload)
        dispatched += 1

    return dispatched
