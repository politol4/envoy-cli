"""CLI commands for the watch feature."""

import argparse
from typing import Optional

from envoy_cli.watch import FileWatcher, WatchError


def _make_watcher(
    path: str,
    callback,
    interval: float,
) -> FileWatcher:
    """Thin factory so tests can patch it easily."""
    return FileWatcher(path=path, callback=callback, interval=interval)


def cmd_watch(
    args: argparse.Namespace,
    manager,
    *,
    max_iterations: Optional[int] = None,
) -> str:
    """
    Watch *args.file* and import it into *args.env* on every modification.

    Parameters
    ----------
    args:
        Namespace with attributes: file (str), env (str), interval (float).
    manager:
        A SyncManager (or compatible) instance.
    max_iterations:
        Cap the polling loop (used in tests to avoid infinite loops).
    """
    from envoy_cli.import_secrets import import_from_file

    env_path: str = args.file
    env_name: str = args.env
    interval: float = getattr(args, "interval", 1.0)
    fmt: str = getattr(args, "fmt", "dotenv")

    def _on_change(path: str) -> None:
        import_from_file(
            manager=manager,
            env=env_name,
            file_path=path,
            fmt=fmt,
            overwrite=True,
        )

    watcher = _make_watcher(path=env_path, callback=_on_change, interval=interval)

    # Prime baseline silently.
    import os

    try:
        watcher._last_mtime = os.path.getmtime(env_path)
    except FileNotFoundError:
        raise WatchError(f"file not found: {env_path}")

    watcher.start(max_iterations=max_iterations)
    return f"Stopped watching '{env_path}' for env '{env_name}'."
