# 工作流节点：与 core/components 注册表对应，供执行器调用
from app.core.workflow.nodes.base_node import BaseNode
from app.core.workflow.nodes.start_node import StartNode
from app.core.workflow.nodes.end_node import EndNode
from app.core.workflow.nodes.llm_node import LLMNode
from app.core.workflow.nodes.rag_node import RAGNode
from app.core.workflow.nodes.tool_node import ToolNode
from app.core.workflow.nodes.agent_node import AgentNode
from app.core.workflow.nodes.condition_node import ConditionNode
from app.core.workflow.nodes.code_node import CodeNode

# type_id -> 节点实例，执行器通过此表调用 run()
NODE_REGISTRY: dict[str, BaseNode] = {
    StartNode.type_id: StartNode(),
    EndNode.type_id: EndNode(),
    LLMNode.type_id: LLMNode(),
    RAGNode.type_id: RAGNode(),
    ToolNode.type_id: ToolNode(),
    AgentNode.type_id: AgentNode(),
    ConditionNode.type_id: ConditionNode(),
    CodeNode.type_id: CodeNode(),
}


def get_node(type_id: str) -> BaseNode | None:
    return NODE_REGISTRY.get(type_id)


__all__ = [
    "BaseNode",
    "StartNode",
    "EndNode",
    "LLMNode",
    "RAGNode",
    "ToolNode",
    "AgentNode",
    "ConditionNode",
    "CodeNode",
    "NODE_REGISTRY",
    "get_node",
]
