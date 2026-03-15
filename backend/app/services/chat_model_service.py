"""聊天模型配置：从 DB 读取 api_host、api_key 等"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.chat_model import ChatModel


async def get_chat_model_by_id(db: AsyncSession, model_id: int) -> ChatModel | None:
    """按 id 获取一条模型配置。"""
    r = await db.execute(select(ChatModel).where(ChatModel.id == model_id))
    return r.scalar_one_or_none()


async def get_chat_model_by_name(db: AsyncSession, model_name: str) -> ChatModel | None:
    """按 model_name 获取一条模型配置。"""
    if not (model_name or "").strip():
        return None
    r = await db.execute(select(ChatModel).where(ChatModel.model_name == model_name.strip()))
    return r.scalar_one_or_none()


async def get_chat_model(db: AsyncSession, model_id: int | None, model_name: str | None) -> ChatModel | None:
    """优先按 model_id 查，否则按 model_name 查。"""
    if model_id is not None:
        return await get_chat_model_by_id(db, model_id)
    if model_name:
        return await get_chat_model_by_name(db, model_name)
    return None


def normalize_api_host(host: str | None) -> str:
    """去掉末尾斜杠，保证 base_url 规范。"""
    if not host or not host.strip():
        return ""
    return host.strip().rstrip("/")
