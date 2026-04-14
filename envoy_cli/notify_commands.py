"""CLI commands for managing notification configs."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from envoy_cli.notify import NotifyConfig, NotifyError


def _notify_path(env: str, base_dir: str = ".") -> Path:
    return Path(base_dir) / ".envoy" / f"{env}.notify.json"


def _load_configs(path: Path) -> List[NotifyConfig]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return [NotifyConfig.from_dict(item) for item in raw]


def _save_configs(path: Path, configs: List[NotifyConfig]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([c.to_dict() for c in configs], fh, indent=2)


def cmd_notify_add(args) -> str:
    """Add or replace a notification config for an env."""
    try:
        cfg = NotifyConfig(
            channel=args.channel,
            target=args.target,
            events=args.events or [],
            enabled=True,
        )
    except Exception as exc:  # pragma: no cover
        raise NotifyError(str(exc)) from exc

    path = _notify_path(args.env, getattr(args, "base_dir", "."))
    configs = _load_configs(path)
    configs = [c for c in configs if not (c.channel == cfg.channel and c.target == cfg.target)]
    configs.append(cfg)
    _save_configs(path, configs)
    return f"Notification config added for env '{args.env}' (channel={cfg.channel})."


def cmd_notify_remove(args) -> str:
    """Remove a notification config by channel + target."""
    path = _notify_path(args.env, getattr(args, "base_dir", "."))
    configs = _load_configs(path)
    before = len(configs)
    configs = [c for c in configs if not (c.channel == args.channel and c.target == args.target)]
    if len(configs) == before:
        raise NotifyError("No matching notification config found.")
    _save_configs(path, configs)
    return f"Notification config removed for env '{args.env}'."


def cmd_notify_list(args) -> str:
    """List all notification configs for an env."""
    path = _notify_path(args.env, getattr(args, "base_dir", "."))
    configs = _load_configs(path)
    if not configs:
        return f"No notification configs for env '{args.env}'."
    lines = [f"Notifications for '{args.env}':"]
    for cfg in configs:
        status = "on" if cfg.enabled else "off"
        events = ", ".join(cfg.events) if cfg.events else "all"
        lines.append(f"  [{status}] {cfg.channel} -> {cfg.target}  events={events}")
    return "\n".join(lines)
