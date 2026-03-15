# 工作流组件说明（LangChain 封装）

## 组件列表

| type_id   | 说明           | 依赖               | 运行时注入 |
|-----------|----------------|--------------------|------------|
| start     | 入口           | -                  | -          |
| end       | 出口           | -                  | _upstream_output |
| llm       | 大模型调用     | langchain-openai   | 可选 llms\[model_name\]、base_url/api_key |
| rag       | 知识库检索     | langchain_core     | retrievers\[retriever_key\] |
| tool      | 单工具调用     | langchain_core     | tools\[tool_name\] 或 tools 列表 |
| agent     | ReAct 智能体   | langgraph.prebuilt | llms、tools（同 llm/tool） |
| condition | 条件分支       | -                  | -          |
| code      | Python 代码    | -                  | -          |

## 使用方式

### 1. 组件 Schema（前端/API）

```python
from app.core.components import list_components, get_component

# 列出所有组件
for c in list_components():
    print(c.type_id, c.name, c.category)

# 获取单个组件 Schema
schema = get_component("llm")
print(schema.config_schema)
```

### 2. 执行图

```python
from app.core.workflow.executor import run_graph

graph = {
    "nodes": [
        {"id": "n1", "type": "start"},
        {"id": "n2", "type": "llm", "config": {"model_name": "gpt-4", "temperature": 0.7}},
        {"id": "n3", "type": "end"},
    ],
    "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
    ],
}

runtime = {
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-...",
    # 或预先构造：llms={"gpt-4": ChatOpenAI(...)}
}

state = run_graph(graph, inputs={"messages": [{"role": "user", "content": "Hello"}]}, runtime=runtime)
print(state["n2"]["text"])
```

### 3. 运行时注入（与 DB 对接）

- **LLM**：在 API 层从 `chat_model` 表查 `api_host`/`api_key`，构造 `ChatOpenAI` 放入 `runtime["llms"][model_name]` 或 `runtime["base_url"]`/`runtime["api_key"]`。
- **RAG**：从 dataset 构建 Retriever（向量库 + Embedding），放入 `runtime["retrievers"][retriever_key]`。
- **Tool**：将平台工具（如 web_search、calculator）转为 LangChain `BaseTool`，放入 `runtime["tools"][tool_name]`。

### 4. Agent 节点

依赖 `langgraph.prebuilt.create_react_agent`；若未安装则退化为单轮 LLM 调用。配置 `tool_keys` 指定要使用的工具 key 列表。
