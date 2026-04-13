"""Webhook notification support for envoy-cli.

Allows users to register HTTP endpoints that receive a POST request
whenever a secret is mutated (set, delete, rotate, import).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


class WebhookError(Exception):
    """Raised when a webhook operation fails."""


@dataclass
class WebhookConfig:
    url: str
    events: List[str] = field(default_factory=list)  # empty = all events
    secret_header: Optional[str] = None  # optional HMAC or bearer token header
    timeout: int = 5

    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "events": self.events,
            "secret_header": self.secret_header,
            "timeout": self.timeout,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "WebhookConfig":
        for key in ("url",):
            if key not in data:
                raise WebhookError(f"Missing required field: {key}")
        return cls(
            url=data["url"],
            events=data.get("events", []),
            secret_header=data.get("secret_header"),
            timeout=int(data.get("timeout", 5)),
        )


def _build_payload(event: str, env: str, key: Optional[str], meta: Dict) -> bytes:
    payload = {
        "event": event,
        "env": env,
        "key": key,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **meta,
    }
    return json.dumps(payload).encode()


def dispatch(config: WebhookConfig, event: str, env: str,
             key: Optional[str] = None, meta: Optional[Dict] = None) -> None:
    """Send a webhook notification if the event matches the config filter."""
    if config.events and event not in config.events:
        return

    body = _build_payload(event, env, key, meta or {})
    headers = {"Content-Type": "application/json"}
    if config.secret_header:
        k, _, v = config.secret_header.partition(":")
        headers[k.strip()] = v.strip()

    req = urllib.request.Request(config.url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.timeout):
            pass
    except urllib.error.URLError as exc:
        raise WebhookError(f"Webhook delivery failed for {config.url!r}: {exc}") from exc


def dispatch_all(configs: List[WebhookConfig], event: str, env: str,
                 key: Optional[str] = None, meta: Optional[Dict] = None) -> List[str]:
    """Dispatch to all configs; return list of error messages (non-fatal)."""
    errors: List[str] = []
    for cfg in configs:
        try:
            dispatch(cfg, event, env, key, meta)
        except WebhookError as exc:
            errors.append(str(exc))
    return errors
