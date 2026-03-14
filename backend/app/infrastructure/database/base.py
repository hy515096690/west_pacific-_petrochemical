"""SQLAlchemy Declarative Base，供所有 ORM 模型继承。"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM 基类。"""
    pass
