"""Master-password based encryption for vault secrets (Fernet)."""
from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KDF_ITERATIONS = 390_000


def derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def new_salt() -> bytes:
    return os.urandom(16)


def encrypt(master_password: str, salt: bytes, plaintext: str) -> str:
    f = Fernet(derive_key(master_password, salt))
    return f.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(master_password: str, salt: bytes, token: str) -> str:
    f = Fernet(derive_key(master_password, salt))
    try:
        return f.decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("invalid master password or corrupted secret") from exc


def fingerprint(master_password: str, salt: bytes) -> str:
    """Non-reversible check that master password matches vault."""
    material = derive_key(master_password, salt)
    return hashlib.sha256(material).hexdigest()
