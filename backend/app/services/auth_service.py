"""认证：登录校验、签发 token"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.user import User
from app.services.user_service import get_user_by_name_or_email, user_to_response
from app.utils.security import create_access_token, verify_password


async def login(db: AsyncSession, username: str, password: str) -> tuple[User, str] | None:
    """
    校验用户名/邮箱 + 明文密码，通过则返回 (user, access_token)。
    失败返回 None。
    """
    user = await get_user_by_name_or_email(db, username)
    if not user or not verify_password(password, user.password):
        return None
    token = create_access_token(sub=user.id)
    return user, token
