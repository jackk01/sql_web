import base64
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet

from app.core.config import get_settings


def hash_password(password: str, *, salt: bytes | None = None) -> tuple[str, str]:
    salt_value = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_value,
        310_000,
    )
    return derived.hex(), base64.b64encode(salt_value).decode("utf-8")


def verify_password(password: str, password_hash: str, password_salt: str) -> bool:
    salt = base64.b64decode(password_salt.encode("utf-8"))
    recalculated_hash, _ = hash_password(password, salt=salt)
    return hmac.compare_digest(recalculated_hash, password_hash)


def encrypt_secret(value: str) -> str:
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")


def _get_fernet() -> Fernet:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    if settings.app_encryption_key:
        key = settings.app_encryption_key.encode("utf-8")
        return Fernet(key)

    if settings.encryption_key_path.exists():
        key = settings.encryption_key_path.read_text(encoding="utf-8").strip().encode("utf-8")
        return Fernet(key)

    key = Fernet.generate_key()
    settings.encryption_key_path.write_text(key.decode("utf-8"), encoding="utf-8")
    return Fernet(key)

