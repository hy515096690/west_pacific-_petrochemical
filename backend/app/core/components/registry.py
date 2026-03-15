"""组件注册表：内置组件 Schema 与运行时节点映射"""
from typing import Any

from app.core.components.schemas import ComponentSchema, ConfigFieldDef, PortDef

# ---------------------------------------------------------------------------
# 内置组件 Schema 定义（与 workflow/nodes 实现一一对应）
# ---------------------------------------------------------------------------

COMPONENT_START = ComponentSchema(
    type_id="start",
    name="开始",
    category="io",
    description="工作流入口，将输入写入 state",
    input_ports=[],
    output_ports=[
        PortDef(name="input", type="object", description="工作流输入"),
    ],
    config_schema=[],
)

COMPONENT_END = ComponentSchema(
    type_id="end",
    name="结束",
    category="io",
    description="工作流出口，将上游结果作为输出",
    input_ports=[
        PortDef(name="input", type="any", required=True, description="上游节点输出"),
    ],
    output_ports=[
        PortDef(name="output", type="object", description="最终输出"),
    ],
    config_schema=[],
)

COMPONENT_LLM = ComponentSchema(
    type_id="llm",
    name="大模型",
    category="llm",
    description="调用大模型生成回复，支持从 chat_model 表解析或直接配置 base_url/api_key",
    input_ports=[
        PortDef(name="messages", type="messages", required=True, description="对话消息列表"),
        PortDef(name="system_prompt", type="string", description="系统提示"),
    ],
    output_ports=[
        PortDef(name="message", type="message", description="最后一条 AI 消息"),
        PortDef(name="text", type="string", description="最后一条消息的文本内容"),
    ],
    config_schema=[
        ConfigFieldDef(name="model_name", type="string", required=True, description="模型名称，对应 chat_model 表或直接使用"),
        ConfigFieldDef(name="temperature", type="number", default=0.7, description="温度"),
        ConfigFieldDef(name="max_tokens", type="number", default=2048, description="最大 token"),
        ConfigFieldDef(name="system_prompt", type="string", description="系统提示（可覆盖输入端口）"),
    ],
)

COMPONENT_RAG = ComponentSchema(
    type_id="rag",
    name="知识库检索",
    category="rag",
    description="从向量库检索文档片段，需在运行时注入 retriever",
    input_ports=[
        PortDef(name="query", type="string", required=True, description="检索 query"),
    ],
    output_ports=[
        PortDef(name="documents", type="object", description="检索到的文档列表"),
        PortDef(name="context", type="string", description="拼接后的上下文文本"),
    ],
    config_schema=[
        ConfigFieldDef(name="retriever_key", type="string", required=True, description="运行时 state._runtime.retrievers 的 key"),
        ConfigFieldDef(name="top_k", type="number", default=5, description="返回条数"),
    ],
)

COMPONENT_TOOL = ComponentSchema(
    type_id="tool",
    name="工具调用",
    category="tool",
    description="调用单个 LangChain 工具",
    input_ports=[
        PortDef(name="tool_input", type="object", required=True, description="工具输入（一般为 dict）"),
    ],
    output_ports=[
        PortDef(name="result", type="any", description="工具返回结果"),
    ],
    config_schema=[
        ConfigFieldDef(name="tool_name", type="string", required=True, description="工具名，对应 _runtime.tools 的 key"),
    ],
)

COMPONENT_AGENT = ComponentSchema(
    type_id="agent",
    name="ReAct 智能体",
    category="agent",
    description="LangChain ReAct Agent，可配置 LLM 与工具列表",
    input_ports=[
        PortDef(name="message", type="string", required=True, description="用户输入或上游文本"),
        PortDef(name="messages", type="messages", description="多轮消息（可选）"),
    ],
    output_ports=[
        PortDef(name="message", type="message", description="Agent 最终回复"),
        PortDef(name="text", type="string", description="回复文本"),
        PortDef(name="intermediate_steps", type="object", description="中间步骤（tool calls）"),
    ],
    config_schema=[
        ConfigFieldDef(name="model_name", type="string", required=True, description="模型名称"),
        ConfigFieldDef(name="tool_keys", type="array", description="工具 key 列表，对应 _runtime.tools"),
        ConfigFieldDef(name="max_iterations", type="number", default=10, description="最大推理步数"),
    ],
)

COMPONENT_CONDITION = ComponentSchema(
    type_id="condition",
    name="条件分支",
    category="logic",
    description="根据表达式或字段值选择出口",
    input_ports=[
        PortDef(name="value", type="any", description="待判断的值"),
        PortDef(name="condition_result", type="string", description="预计算的结果：true/false/分支名"),
    ],
    output_ports=[
        PortDef(name="true", type="any", description="条件为真时的输出"),
        PortDef(name="false", type="any", description="条件为假时的输出"),
    ],
    config_schema=[
        ConfigFieldDef(name="expression", type="string", description="简单表达式，如 state.node_id.field == 'x'"),
        ConfigFieldDef(name="true_branch", type="string", default="true", description="真分支 handle 名"),
        ConfigFieldDef(name="false_branch", type="string", default="false", description="假分支 handle 名"),
    ],
)

COMPONENT_CODE = ComponentSchema(
    type_id="code",
    name="Python 代码",
    category="code",
    description="执行一段 Python，入参 state，返回 dict 合并到本节点输出",
    input_ports=[
        PortDef(name="state", type="object", description="上游 state 引用（由执行器注入）"),
    ],
    output_ports=[
        PortDef(name="result", type="object", description="代码返回的 dict"),
    ],
    config_schema=[
        ConfigFieldDef(name="code", type="code", required=True, description="def main(state: dict) -> dict"),
    ],
)

# ---------------------------------------------------------------------------
# 注册表：type_id -> (schema, handler_path)
# handler_path 指向 workflow.nodes 下的 run 函数，如 app.core.workflow.nodes.llm_node.run
# ---------------------------------------------------------------------------

BUILTIN_COMPONENTS: list[ComponentSchema] = [
    COMPONENT_START,
    COMPONENT_END,
    COMPONENT_LLM,
    COMPONENT_RAG,
    COMPONENT_TOOL,
    COMPONENT_AGENT,
    COMPONENT_CONDITION,
    COMPONENT_CODE,
]

_REGISTRY: dict[str, ComponentSchema] = {c.type_id: c for c in BUILTIN_COMPONENTS}


def get_component(type_id: str) -> ComponentSchema | None:
    """按 type_id 获取组件 Schema。"""
    return _REGISTRY.get(type_id)


def list_components(category: str | None = None) -> list[ComponentSchema]:
    """列出所有已注册组件，可按 category 过滤。"""
    if category is None:
        return list(_REGISTRY.values())
    return [c for c in _REGISTRY.values() if c.category == category]


def get_registry() -> dict[str, ComponentSchema]:
    """返回完整 type_id -> schema 映射（只读）。"""
    return dict(_REGISTRY)


def register_component(schema: ComponentSchema) -> None:
    """注册一个组件（可用于自定义组件）。"""
    _REGISTRY[schema.type_id] = schema
