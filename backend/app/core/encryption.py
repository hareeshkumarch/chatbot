import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import get_settings


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_cipher() -> Fernet:
    settings = get_settings()
    return Fernet(_derive_key(settings.encryption_key))


def encrypt_payload(plaintext: str) -> str:
    return get_cipher().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_payload(ciphertext: str) -> str:
    return get_cipher().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
