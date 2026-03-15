# API v1：汇总路由
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.api.v1 import auth, chat, users

router = APIRouter(prefix="/api/v1", tags=["v1"])

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(chat.router)


@router.get("/health")
def v1_health():
    """API v1 健康检查。"""
    return {"status": "ok", "version": "v1"}


@router.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    """检查数据库与 pgvector 扩展是否可用。"""
    await db.execute(text("SELECT 1"))
    row = await db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    has_vector = row.scalar() is not None
    return {"status": "ok", "database": "postgresql", "pgvector": "enabled" if has_vector else "not_loaded"}
