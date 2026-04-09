"""Sync manager: push/pull .env variables between local vault and remote."""

import os
from typing import Optional

from envoy_cli.vault import Vault
from envoy_cli.remote import RemoteClient
from envoy_cli.diff import compute_diff, DiffResult


class SyncManager:
    """Coordinates push/pull operations between a local Vault and a RemoteClient."""

    def __init__(
        self,
        vault_dir: str,
        client: RemoteClient,
        passphrase: str,
        environment: str = "production",
    ) -> None:
        self.vault_dir = vault_dir
        self.client = client
        self.passphrase = passphrase
        self.environment = environment

    def _vault_path(self) -> str:
        return os.path.join(self.vault_dir, f"{self.environment}.vault")

    def _load_vault(self) -> Vault:
        vault = Vault(self._vault_path(), self.passphrase)
        vault.load()
        return vault

    def push(self) -> None:
        """Encrypt local vault contents and upload to remote."""
        vault = self._load_vault()
        ciphertext = vault.export_ciphertext()
        if not ciphertext:
            raise ValueError("Vault is empty or could not be serialized.")
        self.client.push(self.environment, ciphertext)

    def pull(self) -> None:
        """Download remote ciphertext and merge into local vault."""
        ciphertext = self.client.pull(self.environment)
        vault = Vault(self._vault_path(), self.passphrase)
        vault.import_ciphertext(ciphertext)
        vault.save()

    def diff(self, mask_values: bool = True) -> DiffResult:
        """Return a DiffResult comparing local vault to remote state."""
        local_vault = self._load_vault()
        local_vars = dict(local_vault.all())

        ciphertext = self.client.pull(self.environment)
        remote_vault = Vault(self._vault_path() + ".tmp", self.passphrase)
        remote_vault.import_ciphertext(ciphertext)
        remote_vars = dict(remote_vault.all())

        return compute_diff(local_vars, remote_vars)

    def status(self, mask_values: bool = True) -> str:
        """Return a human-readable status string comparing local to remote."""
        result = self.diff(mask_values=mask_values)
        lines = [f"Environment: {self.environment}", result.summary()]
        lines += result.as_lines(mask_values=mask_values)
        return "\n".join(lines)
