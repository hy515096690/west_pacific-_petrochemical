# 接口鉴权方式与请求示例

## 分层约定（接口层 vs 服务层）

- **接口层（api/v1/）**：只做 HTTP 相关——解析请求、**鉴权依赖（三种方式均在此层）**、调用 service、把结果/异常转成 HTTP 响应。**不直接写 `select`/`execute`/`add` 等数据库操作。**
- **服务层（services/）**：所有业务逻辑与**数据库操作**集中在这里（查库、改库、事务边界）。接口层把 `db` 会话和参数传给 service，由 service 返回结果或抛出业务异常（如 `UserAlreadyExistsError`），接口层只负责把异常映射为 HTTP 状态码（如 400）。

这样职责清晰：接口层不碰 ORM/SQL，后续改表或换库只需改 services 层。

**与鉴权的关系**：三种鉴权方式（仅 JWT、仅 API Key、JWT 或 API Key）全部在**接口层**通过 `Depends(get_current_user)` / `Depends(require_api_key_only(...))` / `Depends(require_auth(...))` 完成，与「接口层 / 服务层分离」无冲突。鉴权通过后，接口层把 `db` 和（按需）当前用户等信息传给 services，services 只做业务与数据库访问，不关心请求是用 JWT 还是 API Key 进来的。

---

## 一、三种鉴权方式对照

| 鉴权方式 | 请求头 | 适用接口 | 后端依赖写法 |
|----------|--------|----------|--------------|
| **1. 仅 JWT** | `Authorization: Bearer <token>` | 登录用户操作（如创建用户、管理 key） | `Depends(get_current_user)` |
| **2. 仅 API Key** | `X-API-Key: <key>` | 仅第三方用 key 调用 | `Depends(require_api_key_only(scopes=["模块名"]))` |
| **3. JWT 或 API Key** | 任一带其一 | 同一接口既给前端又给第三方 | `Depends(require_auth(scopes=["模块名"]))` |

---

## 二、请求格式与示例

### 1. 仅 JWT（Bearer Token）

**请求头：**
```http
Authorization: Bearer <登录后获得的 access_token>
Content-Type: application/json
```

**示例：获取当前用户** `GET /api/v1/auth/me`
```bash
curl -X GET "http://0.0.0.0:8866/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzczNTAyNDE2LCJpYXQiOjE3NzM0OTg4MTZ9.UXajQaIA1WWKaDaHm7wEXBqGRMM77sp4TuLlSKVSx5Y" \
  -H "Content-Type: application/json"
```

**示例：创建用户** `POST /api/v1/users`（需鉴权）
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/users" \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "newuser",
    "email": "new@example.com",
    "password": "123456",
    "create_by": "admin",
    "update_by": "admin"
  }'
```

---

### 2. 仅 API Key（X-API-Key）

**请求头：**
```http
X-API-Key: <用户生成的 API Key 明文>
Content-Type: application/json
```

**示例：** 假设某接口仅允许 API Key，且需要 scope `chat`
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/chat/completions" \
  -H "X-API-Key: wp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

**说明：** 后端只认 `X-API-Key`，不认 `Authorization: Bearer`；key 的 scopes 需包含该接口要求的模块（如 `chat`）。

---

### 3. JWT 或 API Key 二选一

**请求头（两种任选一种即可）：**

- 方式 A：JWT  
  ```http
  Authorization: Bearer <access_token>
  ```

- 方式 B：API Key  
  ```http
  X-API-Key: <api_key>
  ```

**示例 A：用 JWT 调**
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/datasets/query" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"keyword": "检索词"}'
```

**示例 B：用 API Key 调（同一接口）**
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/datasets/query" \
  -H "X-API-Key: wp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "检索词"}'
```

---

## 三、免鉴权接口（不带头）

**示例：登录**
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "haoy", "password": "123456"}'
```

**示例：注册**
```bash
curl -X POST "http://0.0.0.0:8866/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "haoy",
    "email": "haoy@example.com",
    "password": "123456",
    "create_by": "system",
    "update_by": "system"
  }'
```

**示例：健康检查**
```bash
curl -X GET "http://0.0.0.0:8866/health"
```

---

## 四、前端 / 第三方配置小结

| 场景 | 请求头 |
|------|--------|
| 前端已登录 | `Authorization: Bearer <access_token>` |
| 第三方平台 | `X-API-Key: <配置的 key>` |
| 同一接口两种都支持 | 任一带 `Authorization: Bearer ...` 或 `X-API-Key: ...` |
| 公开接口 | 不带上述任一 |

**注意：**  
- JWT 从登录接口 `POST /api/v1/auth/login` 的响应里取 `access_token`。  
- API Key 从「用户生成 API Key」功能获得，创建时返回明文 key，只显示一次，需妥善保存。

---

## 五、Python 接口实现样例（均在接口层，鉴权 + 调 services）

以下为**接口层**（api/v1/）路由写法：鉴权通过 `Depends(...)` 在接口层完成，业务与数据库操作在 services 层；接口层只负责调用 service、把业务异常转为 HTTP 状态码。三种鉴权方式与「接口/服务分层」无冲突。

### 1. 仅 JWT（必须登录）

只认 `Authorization: Bearer <token>`，未带或无效返回 401。

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.db.user import User
from app.models.schema.user_schema import UserCreate, UserResponse
from app.services.user_service import UserAlreadyExistsError, create_user, user_to_response

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """仅登录用户可访问；无 DB 操作，直接返回当前用户信息。"""
    return user_to_response(current_user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_api(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建用户：接口层只做鉴权 + 调 service + 把业务异常转 400。"""
    try:
        user = await create_user(db, body)  # 所有 DB 操作在 service 内
    except UserAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名或邮箱已存在")
    return user_to_response(user)
```

### 2. 仅 API Key（仅第三方 key）

只认 `X-API-Key`，且校验 key 的 scopes 是否包含接口要求的模块。鉴权在接口层完成，业务逻辑可再交给 service。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_db, require_api_key_only

router = APIRouter()

@router.post("/chat/completions")
async def chat_completions(
    body: ChatBody,
    db: AsyncSession = Depends(get_db),
    current: AuthContext = Depends(require_api_key_only(scopes=["chat"])),
):
    """
    仅允许带 X-API-Key 的请求；key 的 scopes 必须包含 "chat"。
    current.user 为 key 所属用户，current.auth_type == "api_key"，current.scopes 为该 key 的权限列表。
    具体对话逻辑在 service 层实现，接口层只传 db、current.user、body。
    """
    # 示例：result = await chat_service.complete(db, user_id=current.user.id, message=body.message)
    return {"reply": "..."}
```

### 3. JWT 或 API Key 二选一（同一接口两种都支持）

带 JWT 或带 `X-API-Key` 均可；若用 API Key 会按 `scopes` 校验。鉴权在接口层完成，接口层只把 `current.user` 等传给 service，不关心是 JWT 还是 API Key。

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, get_db, require_auth

router = APIRouter()

@router.post("/datasets/query")
async def datasets_query(
    body: QueryBody,
    db: AsyncSession = Depends(get_db),
    current: AuthContext = Depends(require_auth(scopes=["datasets"])),
):
    """
    支持两种方式任一带一种即可：
    - Authorization: Bearer <token>
    - X-API-Key: <key>（且 key 的 scopes 需包含 "datasets"）
    current.user 为当前用户，current.auth_type 为 "jwt" 或 "api_key"。查询逻辑在 service 层，接口层只传 db、current.user、body。
    """
    # 示例：results = await dataset_service.query(db, user_id=current.user.id, keyword=body.keyword)
    return {"results": []}
```

### 4. 免鉴权（不校验 token / key）

不加任何 auth 依赖即可。登录等逻辑在 service 层，接口层只解析请求、调 service、返回响应。

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.auth_service import login
from app.services.user_service import user_to_response

router = APIRouter()

@router.post("/auth/login")
async def login_api(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录：无需鉴权；校验与 token 签发在 auth_service 内完成。"""
    result = await login(db, body.username, body.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    user, access_token = result
    return {"access_token": access_token, "user": user_to_response(user)}


@router.get("/health")
def health():
    """健康检查：无需鉴权，无 DB。"""
    return {"status": "ok"}
```

### 5. 依赖导入汇总（均在接口层使用）

```python
# 仅 JWT，得到 User
from app.api.deps import get_current_user
current_user: User = Depends(get_current_user)

# 仅 API Key，得到 AuthContext，并校验 scopes
from app.api.deps import require_api_key_only, AuthContext
current: AuthContext = Depends(require_api_key_only(scopes=["chat", "datasets"]))

# JWT 或 API Key 二选一，得到 AuthContext
from app.api.deps import require_auth, AuthContext
current: AuthContext = Depends(require_auth(scopes=["datasets"]))

# 免鉴权：不注入 get_current_user / require_auth / require_api_key_only
```

**小结**：三种鉴权方式都在**接口层**通过 `Depends(...)` 完成，与「接口层不写 DB、只调 services」的分层不冲突。鉴权通过后，接口层把 `db`、`current_user`/`current`、请求体等传给 services，由 services 做数据库与业务逻辑。
