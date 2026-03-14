"""用户管理：创建、按用户名/邮箱查询（所有数据库操作集中在此层）"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.user import User
from app.models.schema.user_schema import UserCreate, UserResponse
from app.utils.security import hash_password


class UserAlreadyExistsError(Exception):
    """用户名或邮箱已存在时抛出，由接口层转为 400。"""
    pass


async def exists_user_with_name_or_email(db: AsyncSession, user_name: str, email: str) -> bool:
    """是否存在未删除用户：用户名或邮箱任一命中即返回 True。"""
    r = await db.execute(
        select(User).where(
            (User.user_name == user_name) | (User.email == email),
            User.del_flag == 0,
        )
    )
    return r.scalar_one_or_none() is not None


async def create_user(db: AsyncSession, body: UserCreate) -> User:
    """创建用户，密码哈希后入库。若用户名或邮箱已存在则抛出 UserAlreadyExistsError。"""
    if await exists_user_with_name_or_email(db, body.user_name, body.email):
        raise UserAlreadyExistsError("用户名或邮箱已存在")
    hashed = hash_password(body.password)
    user = User(
        user_name=body.user_name,
        email=body.email,
        password=hashed,
        phone_number=body.phone_number,
        sex=body.sex,
        status=body.status or "0",
        del_flag=0,
        create_by=body.create_by,
        update_by=body.update_by,
        remark=body.remark,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """按 id 查用户，且未删除。"""
    r = await db.execute(
        select(User).where(User.id == user_id, User.del_flag == 0)
    )
    return r.scalar_one_or_none()


async def get_user_by_name_or_email(db: AsyncSession, username: str) -> User | None:
    """按用户名或邮箱查用户，且未删除。"""
    r = await db.execute(
        select(User).where(
            (User.user_name == username) | (User.email == username),
            User.del_flag == 0,
        )
    )
    return r.scalar_one_or_none()


def user_to_response(user: User) -> UserResponse:
    """ORM → 响应 Schema（不含密码）。"""
    return UserResponse(
        id=user.id,
        user_name=user.user_name,
        email=user.email,
        phone_number=user.phone_number,
        sex=user.sex,
        status=user.status,
        del_flag=user.del_flag,
        create_by=user.create_by,
        created_time=user.created_time,
        update_by=user.update_by,
        updated_time=user.updated_time,
        remark=user.remark,
    )
