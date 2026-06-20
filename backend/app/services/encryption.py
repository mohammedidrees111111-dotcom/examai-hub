import os
import base64
import json
from cryptography.fernet import Fernet

_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
_fernet = None

if _ENCRYPTION_KEY:
    try:
        key = base64.urlsafe_b64encode(_ENCRYPTION_KEY.encode().ljust(32)[:32])
        _fernet = Fernet(key)
    except Exception:
        pass


def encrypt_api_key(value: str) -> str:
    if not value:
        return ""
    if _fernet:
        return _fernet.encrypt(value.encode()).decode()
    return base64.b64encode(value.encode()).decode()


def decrypt_api_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    if _fernet:
        try:
            return _fernet.decrypt(encrypted.encode()).decode()
        except Exception:
            return ""
    try:
        return base64.b64decode(encrypted.encode()).decode()
    except Exception:
        return ""


def is_encryption_available() -> bool:
    return _fernet is not None
