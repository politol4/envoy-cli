"""Vault: read/write encrypted .env vault files."""

import json
from pathlib import Path
from typing import Dict

from envoy_cli.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".envoy_vault"


class Vault:
    """Manages an encrypted store of environment variables."""

    def __init__(self, vault_path: str = DEFAULT_VAULT_FILE) -> None:
        self.vault_path = Path(vault_path)
        self._data: Dict[str, str] = {}

    def load(self, passphrase: str) -> None:
        """Load and decrypt the vault from disk."""
        if not self.vault_path.exists():
            self._data = {}
            return
        raw = self.vault_path.read_text(encoding="utf-8").strip()
        if not raw:
            self._data = {}
            return
        plaintext = decrypt(raw, passphrase)
        self._data = json.loads(plaintext)

    def save(self, passphrase: str) -> None:
        """Encrypt and persist the vault to disk."""
        plaintext = json.dumps(self._data)
        encoded = encrypt(plaintext, passphrase)
        self.vault_path.write_text(encoded, encoding="utf-8")

    def set(self, key: str, value: str) -> None:
        """Set an environment variable in the vault."""
        self._data[key] = value

    def get(self, key: str) -> str:
        """Retrieve an environment variable from the vault."""
        if key not in self._data:
            raise KeyError(f"Key '{key}' not found in vault.")
        return self._data[key]

    def delete(self, key: str) -> None:
        """Remove an environment variable from the vault."""
        if key not in self._data:
            raise KeyError(f"Key '{key}' not found in vault.")
        del self._data[key]

    def list_keys(self) -> list:
        """Return all keys stored in the vault."""
        return list(self._data.keys())

    def export(self) -> Dict[str, str]:
        """Return a copy of all vault entries."""
        return dict(self._data)
