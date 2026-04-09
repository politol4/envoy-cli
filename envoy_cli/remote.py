"""Remote profile management: push/pull encrypted .env data to/from a remote store."""

import json
import os
import urllib.request
import urllib.error
from typing import Optional


DEFAULT_TIMEOUT = 10


class RemoteError(Exception):
    """Raised when a remote operation fails."""


class RemoteClient:
    """Thin HTTP client for pushing and pulling encrypted vault payloads."""

    def __init__(self, base_url: str, token: str, timeout: int = DEFAULT_TIMEOUT):
        if not base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid base_url: {base_url!r}")
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, body: Optional[bytes] = None) -> dict:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raise RemoteError(f"HTTP {exc.code} {exc.reason} — {url}") from exc
        except urllib.error.URLError as exc:
            raise RemoteError(f"Connection error: {exc.reason}") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def push(self, profile: str, ciphertext: str) -> dict:
        """Upload an encrypted vault payload for *profile*."""
        payload = json.dumps({"profile": profile, "data": ciphertext}).encode()
        return self._request("PUT", f"/envs/{profile}", body=payload)

    def pull(self, profile: str) -> str:
        """Download and return the encrypted vault payload for *profile*."""
        result = self._request("GET", f"/envs/{profile}")
        if "data" not in result:
            raise RemoteError(f"Response missing 'data' field for profile {profile!r}")
        return result["data"]

    def list_profiles(self) -> list:
        """Return a list of available remote profile names."""
        result = self._request("GET", "/envs")
        return result.get("profiles", [])
