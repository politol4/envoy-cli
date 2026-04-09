"""High-level sync operations: push/pull env profiles using Vault + RemoteClient."""

from pathlib import Path

from envoy_cli.vault import Vault
from envoy_cli.remote import RemoteClient, RemoteError
from envoy_cli.env_file import load_file, save_file


class SyncManager:
    """Orchestrates push/pull between a local Vault and a RemoteClient."""

    def __init__(self, client: RemoteClient, vault_dir: str = "."):
        self.client = client
        self.vault_dir = Path(vault_dir)

    def _vault_path(self, profile: str) -> str:
        return str(self.vault_dir / f".envoy.{profile}.vault")

    # ------------------------------------------------------------------
    # Push
    # ------------------------------------------------------------------

    def push(self, profile: str, passphrase: str) -> None:
        """Encrypt the local vault for *profile* and push it to the remote."""
        vault = Vault(self._vault_path(profile), passphrase)
        vault.load()
        ciphertext = vault.export_ciphertext()
        self.client.push(profile, ciphertext)

    # ------------------------------------------------------------------
    # Pull
    # ------------------------------------------------------------------

    def pull(self, profile: str, passphrase: str) -> None:
        """Pull the remote ciphertext for *profile* and store it locally."""
        ciphertext = self.client.pull(profile)
        vault = Vault(self._vault_path(profile), passphrase)
        vault.import_ciphertext(ciphertext)
        vault.save()

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply(self, profile: str, passphrase: str, env_path: str = ".env") -> None:
        """Decrypt the local vault for *profile* and write a plain .env file."""
        vault = Vault(self._vault_path(profile), passphrase)
        vault.load()
        save_file(env_path, vault.all())

    # ------------------------------------------------------------------
    # Import from .env
    # ------------------------------------------------------------------

    def import_env(self, profile: str, passphrase: str, env_path: str = ".env") -> None:
        """Read a plain .env file and store its contents in the local vault."""
        pairs = load_file(env_path)
        vault = Vault(self._vault_path(profile), passphrase)
        vault.load()
        for key, value in pairs.items():
            vault.set(key, value)
        vault.save()
