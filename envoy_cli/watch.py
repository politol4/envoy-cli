"""Watch a .env file for changes and auto-sync to the vault."""

import os
import time
from typing import Callable, Optional


class WatchError(Exception):
    pass


class FileWatcher:
    """Poll a file for modifications and invoke a callback on change."""

    def __init__(
        self,
        path: str,
        callback: Callable[[str], None],
        interval: float = 1.0,
    ) -> None:
        if not path:
            raise WatchError("path must not be empty")
        if interval <= 0:
            raise WatchError("interval must be positive")
        self.path = path
        self.callback = callback
        self.interval = interval
        self._last_mtime: Optional[float] = None
        self._running = False

    def _current_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.path)
        except FileNotFoundError:
            return None

    def check_once(self) -> bool:
        """Check for a change; return True if the callback was fired."""
        mtime = self._current_mtime()
        if mtime is None:
            return False
        if self._last_mtime is None or mtime != self._last_mtime:
            self._last_mtime = mtime
            if self._last_mtime is not None:  # skip the very first silent init
                self.callback(self.path)
                return True
        return False

    def start(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll until stop() is called or max_iterations reached."""
        self._running = True
        # Prime the baseline without firing the callback.
        self._last_mtime = self._current_mtime()
        iterations = 0
        while self._running:
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(self.interval)
            mtime = self._current_mtime()
            if mtime is not None and mtime != self._last_mtime:
                self._last_mtime = mtime
                self.callback(self.path)
            iterations += 1

    def stop(self) -> None:
        self._running = False


def watch_and_import(
    env_path: str,
    env_name: str,
    passphrase: str,
    vault_dir: str = ".",
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> FileWatcher:
    """Create a FileWatcher that imports the .env file into the vault on change."""
    from envoy_cli.import_secrets import import_from_file
    from envoy_cli.sync import SyncManager

    manager = SyncManager(vault_dir=vault_dir, passphrase=passphrase)

    def _on_change(path: str) -> None:
        import_from_file(
            manager=manager,
            env=env_name,
            file_path=path,
            fmt="dotenv",
            overwrite=True,
        )

    watcher = FileWatcher(path=env_path, callback=_on_change, interval=interval)
    watcher.start(max_iterations=max_iterations)
    return watcher
