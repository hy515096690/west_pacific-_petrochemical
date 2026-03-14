# ORM 模型：统一导入以便 Base.metadata 注册所有表
from app.infrastructure.database.base import Base
from app.models.db.user import User
from app.models.db.dataset import Dataset
from app.models.db.api_key import ApiKey

try:
    from app.models.db.document_chunk import DocumentChunk
except ImportError:
    DocumentChunk = None  # pgvector 未安装时无向量表

__all__ = ["Base", "User", "Dataset", "ApiKey"] + (["DocumentChunk"] if DocumentChunk is not None else [])
