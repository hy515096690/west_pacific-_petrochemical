"""FastAPI 入口：起服务与数据库初始化"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as api_v1_router
from app.infrastructure.database.postgres import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时释放连接池。"""
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="West Pacific Petrochemical API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_v1_router)


@app.get("/health")
def health():
    """根路径健康检查。"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
