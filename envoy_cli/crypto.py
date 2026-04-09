"""Encryption and decryption utilities for .env file secrets."""

import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 200_000


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a passphrase using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(passphrase.encode())


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext and return a base64-encoded ciphertext string.

    Format: base64(salt + nonce + ciphertext)
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode()


def decrypt(encoded: str, passphrase: str) -> str:
    """Decrypt a base64-encoded ciphertext string and return plaintext."""
    try:
        payload = base64.b64decode(encoded.encode())
    except Exception as exc:
        raise ValueError("Invalid ciphertext encoding.") from exc

    if len(payload) < SALT_SIZE + NONCE_SIZE:
        raise ValueError("Ciphertext payload is too short.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]
    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong passphrase or corrupted data.") from exc
    return plaintext.decode()
