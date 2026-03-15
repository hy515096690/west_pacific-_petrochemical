# 智能体低代码 + Python 代码 设计方案（仿 Dify / LangFlow）

基于 LangChain/LangGraph，在现有项目结构上实现：**可视化编排（低代码）** + **Python 代码节点/自定义开发**，支持组件复用与工作流运行。

---

## 一、目标与定位

| 能力 | 说明 |
|------|------|
| **低代码编排** | 拖拽节点、连线成 DAG，配置节点参数即可运行，无需写代码。 |
| **封装组件** | 将 LLM、RAG、Agent、工具、条件、HTTP、代码等封装为「组件」，统一输入/输出与配置 Schema。 |
| **Python 代码** | 支持「代码节点」：用户写 Python 片段，读写工作流状态；支持「自定义组件」：开发新节点并注册到平台。 |
| **与现有结构一致** | 复用 backend 的 `core/workflow`、`core/llm`、`core/rag`、`core/agent`、`core/tools`，API 落在 `api/v1/workflows`、`apps`、`agents` 等。 |

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 前端 (Vue3)                                                              │
│  ├── 应用/工作流列表、编排 Studio（画布 + 组件面板 + 属性配置）              │
│  ├── 运行/调试面板（输入、日志、输出、流式）                                 │
│  └── 知识库/模型/对话 等已有视图                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    REST / SSE (运行工作流、流式输出)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 后端 (FastAPI)                                                            │
│  ├── api/v1/workflows、apps、agents、chat…   ← 已有/扩展                   │
│  ├── services/workflow_service, app_service, run_service                  │
│  └── core/                                                                │
│       ├── workflow/          ← 工作流引擎（DAG 解析、执行调度）             │
│       │   ├── graph/         ← 图定义与 LangGraph 编排（新增）             │
│       │   └── nodes/        ← 节点实现（LLM/RAG/Code/Agent/…）             │
│       ├── llm/、rag/、agent/、tools/  ← 已有，作为节点底层能力              │
│       └── components/       ← 组件注册表与 Schema（新增）                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    读配置、读向量库、调模型、执行代码
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 基础设施：DB(PostgreSQL+pgvector)、Redis、向量库、对象存储、chat_model 表   │
└─────────────────────────────────────────────────────────────────────────┘
```

- **低代码**：前端画布编辑「图」→ 存为 workflow 定义（JSON）→ 运行由 backend 解析图并执行。
- **组件**：每个节点类型对应一个「组件」，后端有统一 Schema（输入/输出/配置），前端按 Schema 渲染表单。
- **Python**：通过「代码节点」内嵌 Python 片段；自定义组件用 Python 开发后注册到 `components`，与现有 `core/workflow/nodes` 对齐。

---

## 三、核心概念

### 3.1 工作流（Workflow）与 应用（App）

- **Workflow**：一次「图」的版本化定义（节点 + 边 + 全局变量），对应 DB 中一条 workflow 定义（如 `workflow_def` 表存 JSON）。
- **App**：对外可用的「应用」，绑定一个 workflow 版本 + 入口节点 + 发布配置；对话/API 触发时跑该 workflow。与现有 `app`、`conversation` 表衔接。

### 3.2 组件（Component）

- **组件** = 节点类型在平台中的抽象：有唯一 `type_id`、输入/输出 Schema、配置 Schema、图标与描述。
- **分类建议**：`llm` | `rag` | `agent` | `tool` | `logic` | `code` | `io` | `extend`。
- **实现**：后端 `core/workflow/nodes` 下每个节点类对应一个组件；`core/components` 维护「组件注册表」和对外 Schema（可 JSON 导出给前端）。

### 3.3 图模型（DAG）

- **节点**：id、type（对应组件 type_id）、name、config（组件所需参数）、position（前端坐标可选）。
- **边**：source_node_id、source_handle、target_node_id、target_handle；可带条件（如 condition 节点多出口）。
- **全局**：variables（工作流级变量）、entry_node_id、output_node_id（可选）。

存储为 JSON，例如：

```json
{
  "nodes": [
    { "id": "n1", "type": "llm", "name": "大模型", "config": { "model": "got-5.2", "prompt": "{{sys.prompt}}" } },
    { "id": "n2", "type": "code", "name": "处理", "config": { "code": "def main(state): return {\"out\": state[\"n1\"][\"text\"]}" } }
  ],
  "edges": [
    { "source": "n1", "target": "n2" }
  ],
  "variables": { "sys.prompt": "" }
}
```

---

## 四、组件体系（封装已有能力 + LangChain）

### 4.1 组件清单（与现有 core 对应）

| 组件 type_id | 说明 | 底层实现 | 输入/输出约定 |
|--------------|------|----------|----------------|
| **llm** | 调用大模型 | `core/llm` + chat_model 表 | in: messages/config → out: message/text |
| **rag** | 检索增强 | `core/rag` pipeline + dataset | in: query → out: docs/context |
| **agent** | ReAct / Plan-Execute | `core/agent` + LangChain Agent | in: message, tools → out: message/steps |
| **tool** | 单工具调用 | `core/tools` | in: tool_name, args → out: result |
| **code** | Python 代码节点 | 安全执行（见下） | in: state → out: 写入 state |
| **condition** | 条件分支 | `core/workflow/nodes/condition_node` | in: condition_expr → out: branch |
| **http** | HTTP 请求 | `core/workflow/nodes/http_node` | in: url/body → out: response |
| **start** / **end** | 入口/出口 | 占位节点 | 仅做拓扑入口/出口 |

### 4.2 组件 Schema 规范（供前端与校验）

每个组件在 backend 注册时提供：

- **type_id**、**name**、**category**、**description**
- **input_schema**：各输入端口名、类型、是否必填、默认值
- **output_schema**：输出端口名与类型
- **config_schema**：节点配置项（如 model、temperature、prompt 模板），可用 JSON Schema 或 Pydantic 描述

示例（LLM 节点）：

```yaml
type_id: llm
name: 大模型
category: llm
input_schema:
  - name: messages; type: messages; required: true
  - name: system_prompt; type: string
config_schema:
  model: string  # 对应 chat_model 表
  temperature: number
  max_tokens: number
output_schema:
  - name: message; type: message
  - name: text; type: string
```

### 4.3 LangChain 集成方式

- **执行层**：用 **LangGraph** 的 `StateGraph` 将「图 JSON」转成可执行图：每个节点对应一个 `state -> state` 的函数，从 state 读上游输出、写当前输出，再交给下一节点。
- **节点实现**：在 `core/workflow/nodes` 中，各节点内部可调用 LangChain 的 `ChatOpenAI`、`Retriever`、`create_react_agent` 等；LLM 的 base_url/api_key 从 `chat_model` 表取（与现有 chat 接口一致）。
- **依赖**：在 `requirements.txt` / `pyproject.toml` 中增加 `langchain`、`langchain-core`、`langgraph` 等，版本与现有 pyproject 一致。

---

## 五、工作流执行引擎

### 5.1 从「图 JSON」到可执行图

- **解析**：将存储的 nodes/edges 转为「节点 id → 入边/出边」的拓扑结构，做 DAG 校验（无环、入口可达）。
- **状态**：全局 state 为 `dict`，key 为节点 id，value 为该节点输出；可约定 `state["_input"]` 为工作流输入，`state["_output"]` 为最终输出。
- **执行**：
  - **方案 A**：用 LangGraph `StateGraph`：按 nodes/edges 添加 `add_node`、`add_edge`/`add_conditional_edges`，编译后 `graph.invoke(initial_state)`；适合与 LangChain 生态统一。
  - **方案 B**：自研拓扑执行器：按拓扑序依次调用各节点函数，传入当前 state，节点返回 delta 合并进 state；与现有 `core/workflow/executor.py` 一致，便于和现有节点实现对接。

建议：**先 B 保证与现有 nodes 兼容，再在关键链路上用 LangGraph（如 Agent 子图）**。

### 5.2 节点执行契约

- **输入**：从 `state` 中按边关系取上游节点输出（如 `state["n1"]`）；若节点声明了输入变量名，可从 `state["_input"]` 或全局 variables 取。
- **输出**：节点返回 `dict`，执行器合并到 `state[node_id]`；约定如 `{"text": "...", "message": {...}}` 供下游引用。
- **异常**：节点抛出异常即终止运行，返回错误信息与已执行到的节点 id，便于调试。

### 5.3 流式输出

- 若终点是 LLM 或 Agent，需要流式：可在该节点内使用 `yield` 或 callback 将 token 通过 SSE 推给前端；或在工作流层识别「流式节点」，对其单独走流式通道（与现有 chat 流式一致）。

---

## 六、Python 代码节点（低代码里的「代码」）

### 6.1 能力

- 用户在图里添加「代码节点」，在配置中写一段 Python 函数（如 `def main(state: dict) -> dict`）。
- 执行时由 backend 在**受控环境**中执行该函数：只注入 `state`，返回值合并回 state；禁止文件、网络、子进程等（白名单或沙箱）。

### 6.2 安全与实现

- **沙箱**：使用 `RestrictedPython` 或子进程 + 超时 + 禁用危险 builtins；或 Docker 短时容器执行（实现成本高，可二期）。
- **API**：`state` 只读或拷贝传入，返回 `dict` 即该节点输出；支持在代码中读 `state["n1"]`、写 `return {"result": ...}`。
- **依赖**：代码节点内不开放任意 import，仅可用的「内置」由平台注入（如 `json`、`re`、或平台提供的 `llm_call` 等）。

### 6.3 与「自定义组件」的区别

- **代码节点**：单节点内写逻辑，不改图结构，适合简单处理、格式化、分支逻辑。
- **自定义组件**：用 Python 在 `core/workflow/nodes` 或 `core/components` 中开发新节点类型，实现固定接口并注册到组件表；适合复用、发布给他人使用。

---

## 七、数据模型（与现有 DB 对齐）

### 7.1 新增/扩展表建议

| 表名 | 用途 |
|------|------|
| **workflow_def** | 工作流定义：id、name、description、graph_json、version、created_by、created_at 等；可与现有 `workflow` 表合并或扩展。 |
| **workflow_run** | 单次运行记录：workflow_def_id、app_id、inputs_json、outputs_json、status、error、started_at、finished_at；便于调试与审计。 |
| **component_registry** | 组件注册：type_id、name、category、input_schema、output_schema、config_schema、handler_path（如 `app.core.workflow.nodes.llm_node.run`）；可为代码表或 JSON 配置。 |

### 7.2 与已有表关系

- **app**：绑定 workflow_def 的某版本，作为「应用」发布；conversation 关联 app，与现有 `app`、`conversation` 表一致。
- **chat_model**：LLM 节点从该表取 api_host、api_key，与现有对话接口一致。
- **dataset**：RAG 节点关联 dataset，与现有知识库一致。

---

## 八、API 设计（对齐现有 api/v1）

### 8.1 工作流与应用

- `GET/POST /api/v1/workflows`：列表、创建 workflow_def。
- `GET/PUT/DELETE /api/v1/workflows/{id}`：单条定义；PUT 可保存新 graph_json 或新版本。
- `POST /api/v1/workflows/{id}/run`：同步执行，body 为 `inputs`，返回 `outputs` 及 run_id。
- `POST /api/v1/workflows/{id}/run/stream`：流式执行，SSE 返回 token 或事件（可选）。
- `GET /api/v1/workflows/runs/{run_id}`：运行状态与结果（从 workflow_run 表读）。

与现有 `workflows.py`、`apps.py` 合并或拆分均可。

### 8.2 组件

- `GET /api/v1/components`：组件列表（从 component_registry 或代码扫描生成），返回 type_id、name、category、schema；供前端画布「组件面板」使用。
- `GET /api/v1/components/{type_id}`：单个组件的 input/output/config schema，供前端渲染节点配置表单。

### 8.3 应用与对话（沿用与扩展）

- 应用发布后，对话接口可走「绑定该应用的 workflow」：即 `POST /api/v1/chat/completions` 或专用 `POST /api/v1/apps/{app_id}/chat`，body 中指定 conversation 或直接传 message，后端解析 app 的 workflow 并执行，返回/流式返回结果。

---

## 九、前端（Vue3）分工

- **工作流 Studio**：画布（拖拽、连线、删除、撤销）、组件面板（按 category 展示，从 `GET /api/v1/components` 拉取）、节点属性面板（按 config_schema 渲染表单）、变量/全局配置区。
- **运行区**：输入表单（对应 workflow 的 variables 或 _input）、运行/停止、日志（按节点展示）、输出/流式展示；可对接 `workflows/{id}/run` 与 `run/stream`。
- **应用/工作流列表**：已有 views 可扩展；新建/编辑跳转 Studio。

技术选型：画布可用 **Vue Flow**、**LogicFlow** 或 **React Flow 的 Vue 移植**，与现有 Vue3 + Pinia 集成。

---

## 十、实施阶段建议

| 阶段 | 内容 |
|------|------|
| **1. 组件与 Schema** | 定义 component_registry 表或 JSON；实现 3～5 个核心组件（start、llm、rag、code、end），统一 input/output/config schema；`GET /api/v1/components` 返回列表与 schema。 |
| **2. 图存储与执行** | workflow_def 存 graph_json；实现 DAG 解析与拓扑执行器，调用现有 nodes；`POST /api/v1/workflows/{id}/run` 跑通端到端。 |
| **3. LangGraph 接入** | 将「图 JSON」转成 LangGraph StateGraph，LLM/Agent 节点用 LangChain；与现有 chat_model、rag 对接；可选替换或并行于自研执行器。 |
| **4. 代码节点与安全** | 实现 code 节点：RestrictedPython 或子进程 + 超时；定义 state 入参与返回约定；在 Studio 中可配置代码片段。 |
| **5. 前端 Studio** | 画布 + 组件面板 + 属性配置 + 运行/调试；与 workflows API 对接。 |
| **6. 应用与对话** | App 绑定 workflow；对话接口支持「按 app 执行 workflow」并支持流式；与 conversation 历史衔接。 |

---

## 十一、与现有目录的对应关系

| 现有路径 | 在本方案中的角色 |
|----------|------------------|
| `core/workflow/nodes/*` | 各节点实现，对应「组件」；需统一接口（如 `run(config, state) -> state_delta`）并注册到组件表。 |
| `core/workflow/executor.py` | 扩展为「图解析 + 拓扑执行」或改为调用 LangGraph 编译后的图。 |
| `core/workflow/dag_builder.py` | 从 graph_json 构建 DAG 或 LangGraph。 |
| `core/llm`、`core/rag`、`core/agent`、`core/tools` | 作为节点底层能力，由对应节点内部调用。 |
| `api/v1/workflows.py`、`apps.py`、`chat.py` | 扩展为上述 workflow/app/run/components API。 |
| `models/db/workflow.py` | 扩展或新增 workflow_def、workflow_run、component_registry。 |

按此方案，可以在不推翻现有结构的前提下，逐步做出「Dify/LangFlow 风格」的低代码 + Python 代码 智能体平台，并与 LangChain/LangGraph 深度结合。
