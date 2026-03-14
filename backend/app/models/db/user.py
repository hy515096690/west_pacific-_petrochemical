"""用户 ORM 模型"""
from datetime import datetime

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dept_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(11), unique=True, nullable=True)
    sex: Mapped[str] = mapped_column(String(1), nullable=False)
    status: Mapped[str | None] = mapped_column(String(1), default=0, nullable=True)
    # 0：正常，1：删除
    del_flag: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    login_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    login_date: Mapped[datetime | None] = mapped_column(nullable=True)
    create_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_time: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    update_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_time: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
