"""CLI commands for managing webhook configurations."""
from __future__ import annotations

import json
import os
from typing import List

from envoy_cli.webhook import WebhookConfig, WebhookError, dispatch


_WEBHOOK_FILE = ".envoy_webhooks.json"


def _webhooks_path(base_dir: str = ".") -> str:
    return os.path.join(base_dir, _WEBHOOK_FILE)


def _load_configs(base_dir: str = ".") -> List[WebhookConfig]:
    path = _webhooks_path(base_dir)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        data = json.load(fh)
    return [WebhookConfig.from_dict(d) for d in data]


def _save_configs(configs: List[WebhookConfig], base_dir: str = ".") -> None:
    path = _webhooks_path(base_dir)
    with open(path, "w") as fh:
        json.dump([c.to_dict() for c in configs], fh, indent=2)


def cmd_webhook_add(args) -> str:
    """Register a new webhook endpoint."""
    events = args.events.split(",") if getattr(args, "events", None) else []
    cfg = WebhookConfig(
        url=args.url,
        events=[e.strip() for e in events if e.strip()],
        secret_header=getattr(args, "secret_header", None),
        timeout=int(getattr(args, "timeout", 5)),
    )
    base_dir = getattr(args, "base_dir", ".")
    configs = _load_configs(base_dir)
    configs.append(cfg)
    _save_configs(configs, base_dir)
    return f"Webhook registered: {cfg.url}"


def cmd_webhook_remove(args) -> str:
    """Remove a webhook by URL."""
    base_dir = getattr(args, "base_dir", ".")
    configs = _load_configs(base_dir)
    before = len(configs)
    configs = [c for c in configs if c.url != args.url]
    if len(configs) == before:
        raise WebhookError(f"No webhook found with URL: {args.url}")
    _save_configs(configs, base_dir)
    return f"Webhook removed: {args.url}"


def cmd_webhook_list(args) -> str:
    """List all registered webhooks."""
    base_dir = getattr(args, "base_dir", ".")
    configs = _load_configs(base_dir)
    if not configs:
        return "No webhooks registered."
    lines = []
    for cfg in configs:
        events = ", ".join(cfg.events) if cfg.events else "all"
        lines.append(f"  {cfg.url}  [events: {events}]  [timeout: {cfg.timeout}s]")
    return "\n".join(lines)


def cmd_webhook_test(args) -> str:
    """Send a test ping to a registered webhook."""
    base_dir = getattr(args, "base_dir", ".")
    configs = _load_configs(base_dir)
    matches = [c for c in configs if c.url == args.url]
    if not matches:
        raise WebhookError(f"No webhook found with URL: {args.url}")
    dispatch(matches[0], event="ping", env="test", key=None, meta={"message": "envoy-cli test ping"})
    return f"Test ping sent to {args.url}"
