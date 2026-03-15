"""聊天模型配置 ORM：模型类别、名称、API 地址与密钥等"""
from datetime import datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ChatModel(Base):
    __tablename__ = "chat_model"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="模型类别")
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="模型名称")
    model_describe: Mapped[str] = mapped_column(String(255), nullable=False, comment="模型描述")
    api_host: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="模型请求地址")
    api_key: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="密钥")
    create_dept_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="创建部门ID")
    create_dept: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="创建部门")
    create_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="创建人ID")
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="创建人")
    create_time: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False, comment="创建时间")
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="更新人")
    update_time: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间"
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")
