# West Pacific Petrochemical

项目骨架：后端 (FastAPI) + 前端 (Vue3) + 部署配置。

## 目录结构

```
├── backend/          # 后端 (FastAPI)
│   ├── app/
│   │   ├── api/      # API 路由 (v1: auth, apps, chat, datasets, workflows, agents, models, files)
│   │   ├── core/     # 核心：LLM、RAG、工作流、Agent、工具
│   │   ├── services/ # 业务服务
│   │   ├── models/   # 数据模型 (db + schema)
│   │   ├── infrastructure/ # 数据库、缓存、向量库、存储、MQ
│   │   └── utils/
│   ├── tests/
│   ├── main.py
│   ├── config.yaml        # 唯一配置文件（无 .env / 无 Python 配置）
│   └── requirements.txt
├── frontend/         # 前端 (Vue3)
│   └── src/
│       ├── views/    # Studio, Workflow, Dataset, ChatWindow
│       ├── components/
│       └── stores/
└── deploy/           # 部署
    ├── docker-compose.yml
    ├── docker-compose.prod.yml
    ├── k8s/
    └── nginx/
```

## 快速开始

### 后端

配置仅使用 **config.yaml**（可复制 `config.yaml.example`）。默认监听 **0.0.0.0:8866**，数据库为本地 PostgreSQL（用户 postgres，库 west-pacific）。

```bash
cd backend
cp config.yaml.example config.yaml   # 按需修改
pip install -r requirements.txt
python main.py
# 或指定 host/port：uvicorn main:app --host 0.0.0.0 --port 8866
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 使用 Docker

```bash
cd deploy
docker-compose up -d
```

## 配置说明

- 所有配置在 **backend/config.yaml**，无 Python 配置文件、无 .env。
- 数据库：PostgreSQL，需安装 [pgvector](https://github.com/pgvector/pgvector) 扩展（启动时自动执行 `CREATE EXTENSION IF NOT EXISTS vector`）。
- 服务默认：**0.0.0.0:8866**（`config.yaml` 中 `server.host` / `server.port`）。

启动后可用接口自检：

- `GET /health` — 存活
- `GET /api/v1/health` — v1 存活
- `GET /api/v1/db-check` — 数据库与 pgvector 是否可用
