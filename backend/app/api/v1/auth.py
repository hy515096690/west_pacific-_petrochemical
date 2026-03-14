"""认证接口：登录、当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.db.user import User
from app.models.schema.user_schema import LoginRequest, LoginResponse, UserCreate, UserResponse
from app.services.auth_service import login
from app.services.user_service import UserAlreadyExistsError, create_user, user_to_response


router = APIRouter(prefix="/auth", tags=["认证"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_api(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需 Bearer token）。"""
    return user_to_response(current_user)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_api(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """注册：创建用户（密码自动 bcrypt 哈希），无需 token。可用于首个用户。"""
    try:
        user = await create_user(db, body)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已存在")
    return user_to_response(user)


@router.post("/login", response_model=LoginResponse)
async def login_api(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录：用户名或邮箱 + 明文密码，返回 access_token 与用户信息。"""
    result = await login(db, body.username, body.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    user, access_token = result
    return LoginResponse(
        access_token=access_token,
        user=user_to_response(user),
    )
