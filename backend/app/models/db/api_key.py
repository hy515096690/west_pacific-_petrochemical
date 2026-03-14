"""API Key ORM 模型：用户生成 key，并配置可调用的模块/接口范围"""
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ApiKey(Base):
    """
    用户创建的 API Key，供第三方凭 key 调用接口。
    key_hash: 只存哈希，明文 key 仅创建时返回一次。
    scopes: 逗号分隔的模块/权限，如 "chat,datasets,workflows"，控制可调用的接口。
    """
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="key 备注名")
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="key 哈希，不存明文")
    scopes: Mapped[str] = mapped_column(String(512), nullable=False, default="", comment="逗号分隔，如 chat,datasets")
    created_time: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_used_time: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(1), default=0, nullable=True, comment="api key状态，0：启用，1：禁用")
    del_flag: Mapped[str] = mapped_column(String(1), default=0, nullable=True, comment="删除状态")
