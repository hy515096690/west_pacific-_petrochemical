"""
依赖注入 (DB / Auth)

鉴权用法：
- 需要登录才能访问：current_user: User = Depends(get_current_user)，未带/无效 token 会 401。
- 不需要鉴权：不加 auth 依赖即可，如 /health、/auth/login、/auth/register。
- 可选鉴权：get_current_user_optional，得到 User | None。
- JWT 或 API Key 二选一（第三方用 key 调接口）：current: AuthContext = Depends(require_auth(scopes=["chat"]))
  - 请求头带 Authorization: Bearer <jwt> 或 X-API-Key: <key> 均可；API Key 会按 scopes 校验可调用的模块。
- 仅允许 API Key（不允许 JWT）：current: AuthContext = Depends(require_api_key_only(scopes=["chat"]))
"""
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.postgres import get_db as _get_db
from app.models.db.api_key import ApiKey
from app.models.db.user import User
from app.services.user_service import get_user_by_id
from app.utils.security import decode_access_token, hash_api_key

security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass
class AuthContext:
    """统一鉴权结果：来自 JWT 或 API Key，便于路由内统一使用。"""
    user: User
    auth_type: str  # "jwt" | "api_key"
    scopes: list[str]  # API Key 时有值，JWT 时为空列表表示全部权限


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """注入异步数据库会话。"""
    async for session in _get_db():
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """鉴权：从 Authorization: Bearer <token> 解析出当前用户，未带或无效则 401。"""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的 token")
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在或已删除")
    return user


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    """可选鉴权：有且有效 token 则返回当前用户，否则返回 None，不抛 401。用于「登录了则带用户信息，未登录也可访问」的接口。"""
    if not credentials or credentials.scheme.lower() != "bearer":
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        return None
    return await get_user_by_id(db, user_id)


# ---------- API Key 与「JWT 或 API Key」统一鉴权 ----------


def _parse_scopes(scopes_str: str) -> list[str]:
    return [s.strip() for s in scopes_str.split(",") if s.strip()]


def _check_scope(required: list[str], user_scopes: list[str], is_jwt: bool) -> bool:
    """JWT 视为拥有全部 scope；API Key 则必须在 user_scopes 内。"""
    if not required:
        return True
    if is_jwt:
        return True
    return all(s in user_scopes for s in required)


async def _get_apikey_user(
    db: AsyncSession,
    key_plain: str | None,
    required_scopes: list[str],
) -> tuple[User, list[str]] | None:
    """校验 X-API-Key，返回 (user, scopes) 或 None。"""
    if not key_plain or not key_plain.strip():
        return None
    key_hash = hash_api_key(key_plain.strip())
    r = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = r.scalar_one_or_none()
    if not api_key:
        return None
    user = await get_user_by_id(db, api_key.user_id)
    if not user:
        return None
    scopes = _parse_scopes(api_key.scopes)
    if not _check_scope(required_scopes, scopes, is_jwt=False):
        return None
    return user, scopes


def require_api_key_only(required_scopes: list[str] | None = None):
    """
    仅允许 API Key，不允许 JWT。用于「仅第三方 key 可调」的接口。
    用法：current: AuthContext = Depends(require_api_key_only(scopes=["chat"]))
    """
    required = required_scopes or []

    async def _dep(
        db: AsyncSession = Depends(get_db),
        api_key: str | None = Depends(api_key_header),
    ) -> AuthContext:
        out = await _get_apikey_user(db, api_key, required)
        if not out:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少或无效的 X-API-Key，或该 key 无权限访问此接口",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        user, scopes = out
        return AuthContext(user=user, auth_type="api_key", scopes=scopes)

    return _dep


def require_auth(required_scopes: list[str] | None = None):
    """
    依赖工厂：接受「JWT 或 API Key」任一方式；API Key 时会校验 required_scopes。
    用法：current: AuthContext = Depends(require_auth(scopes=["chat", "datasets"]))
    """

    async def _require_auth(
        db: AsyncSession = Depends(get_db),
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
        api_key: str | None = Depends(api_key_header),
    ) -> AuthContext:
        required = required_scopes or []
        # 1. 先看 Bearer JWT
        if credentials and credentials.scheme.lower() == "bearer":
            payload = decode_access_token(credentials.credentials)
            if payload and "sub" in payload:
                try:
                    user_id = int(payload["sub"])
                    user = await get_user_by_id(db, user_id)
                    if user:
                        return AuthContext(user=user, auth_type="jwt", scopes=[])
                except (ValueError, TypeError):
                    pass
        # 2. 再看 X-API-Key
        out = await _get_apikey_user(db, api_key, required)
        if out:
            user, scopes = out
            return AuthContext(user=user, auth_type="api_key", scopes=scopes)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请提供有效的 Authorization: Bearer <token> 或 X-API-Key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _require_auth
