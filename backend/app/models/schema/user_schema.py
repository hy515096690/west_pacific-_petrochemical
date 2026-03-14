"""用户与认证相关 Schema"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """创建用户请求（明文密码，入库前哈希）"""
    user_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    phone_number: str | None = Field(None, max_length=11)
    sex: str = Field("0", max_length=1)  # 0未知 1男 2女
    status: str | None = Field("0", max_length=1)  # 0正常 1停用
    create_by: str = Field(..., max_length=64)
    update_by: str = Field(..., max_length=64)
    remark: str | None = None


class UserResponse(BaseModel):
    """用户信息响应（不含密码）"""
    id: int
    user_name: str
    email: str
    phone_number: str | None
    sex: str
    status: str | None
    del_flag: int
    create_by: str
    created_time: datetime
    update_by: str
    updated_time: datetime
    remark: str | None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """登录请求：支持用户名或邮箱 + 明文密码"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """登录成功：token + 用户信息"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
