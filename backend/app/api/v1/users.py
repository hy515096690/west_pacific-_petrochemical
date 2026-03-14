"""用户接口：创建用户（需鉴权）。接口层只做请求/响应与鉴权，数据库操作在 services 层。"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.db.user import User
from app.models.schema.user_schema import UserCreate, UserResponse
from app.services.user_service import UserAlreadyExistsError, create_user, user_to_response

router = APIRouter(prefix="/users", tags=["用户"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_api(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建用户（密码明文传入，入库前在 service 层 bcrypt 哈希）。需登录后 Bearer token 鉴权。"""
    try:
        user = await create_user(db, body)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已存在")
    return user_to_response(user)
