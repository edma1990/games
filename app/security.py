import base64
import hashlib
import hmac

from cryptography.fernet import Fernet

from .config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    if settings.encryption_key:
        key = settings.encryption_key.encode()
    else:
        # Safe enough only for local prototyping; production validates this at startup.
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.app_secret.encode()).digest())
    return Fernet(key)


def encrypt_text(value: str) -> bytes:
    return _fernet().encrypt(value.encode("utf-8"))


def decrypt_text(value: bytes) -> str:
    return _fernet().decrypt(value).decode("utf-8")


def searchable_hash(value: str) -> str:
    secret = get_settings().app_secret.encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()
