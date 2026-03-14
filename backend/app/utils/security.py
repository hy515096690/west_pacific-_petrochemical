"""密码哈希、JWT、API Key 哈希"""
import hashlib
from datetime import datetime, timezone, timedelta

import bcrypt
import jwt

from app.config import settings

# bcrypt 限制密码最长 72 字节
_MAX_PASSWORD_BYTES = 72


def _to_bytes(plain: str) -> bytes:
    raw = plain.encode("utf-8")
    return raw[: _MAX_PASSWORD_BYTES] if len(raw) > _MAX_PASSWORD_BYTES else raw


def hash_password(plain: str) -> str:
    """明文密码 → 存储用 bcrypt 哈希。"""
    return bcrypt.hashpw(_to_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文与哈希是否一致。"""
    return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))


def create_access_token(sub: str | int, extra: dict | None = None) -> str:
    """生成 JWT access token。sub 通常为 user_id。"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(sub),
        "exp": expire,
        "iat": now,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """解析 JWT，失败返回 None。"""
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.PyJWTError:
        return None


def hash_api_key(plain_key: str) -> str:
    """API Key 明文 → 存储用哈希（带 pepper，不可逆）。"""
    raw = f"{settings.secret_key}:{plain_key}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
