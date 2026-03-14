"""仅从 config.yaml 加载配置，供应用使用（无 .env、无 Python 默认值）"""
from pathlib import Path
from types import SimpleNamespace

import yaml


def _find_config_path() -> Path:
    for base in (Path(__file__).resolve().parent.parent, Path.cwd()):
        p = base / "config.yaml"
        if p.exists():
            return p
    raise FileNotFoundError("未找到 config.yaml，请在 backend 目录或项目根目录放置 config.yaml")


def _load_yaml() -> dict:
    with open(_find_config_path(), encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_settings(raw: dict) -> SimpleNamespace:
    app = raw.get("app") or {}
    server = raw.get("server") or {}
    db = raw.get("database") or {}
    redis = raw.get("redis") or {}
    vs = raw.get("vector_store") or {}
    storage = raw.get("storage") or {}
    jwt = raw.get("jwt") or {}

    database_url = (
        f"postgresql://{db.get('user', 'postgres')}:{db.get('password', '')}"
        f"@{db.get('host', 'localhost')}:{db.get('port', 5432)}/{db.get('name', 'west-pacific')}"
    )
    async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
        "postgres://", "postgresql+asyncpg://", 1
    )

    return SimpleNamespace(
        app_name=app.get("name", "West Pacific Petrochemical"),
        debug=app.get("debug", False),
        host=server.get("host", "0.0.0.0"),
        port=int(server.get("port", 8866)),
        database_url=database_url,
        async_database_url=async_database_url,
        redis_url=redis.get("url", "redis://localhost:6379/0"),
        vector_store_type=vs.get("type", "chroma"),
        vector_store_url=vs.get("url", ""),
        minio_endpoint=storage.get("minio_endpoint", "localhost:9000"),
        minio_access_key=storage.get("minio_access_key", ""),
        minio_secret_key=storage.get("minio_secret_key", ""),
        minio_bucket=storage.get("minio_bucket", "default"),
        secret_key=jwt.get("secret_key", "change-me-in-production"),
        algorithm=jwt.get("algorithm", "HS256"),
        access_token_expire_minutes=int(jwt.get("access_token_expire_minutes", 60)),
    )


def get_settings() -> SimpleNamespace:
    return _build_settings(_load_yaml())


# 导入时从 config.yaml 加载，全项目使用此单例
settings = get_settings()
