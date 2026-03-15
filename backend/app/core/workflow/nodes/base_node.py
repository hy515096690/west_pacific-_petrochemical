"""工作流节点基类：统一执行契约 run(config, state) -> state_delta"""
from abc import ABC, abstractmethod
from typing import Any


class BaseNode(ABC):
    """所有工作流节点的抽象基类。"""

    type_id: str = "base"

    @abstractmethod
    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行当前节点。
        :param config: 节点配置（来自图定义中该节点的 config）
        :param state: 当前全局 state（只读，上游节点输出在 state[上游node_id]）
        :param node_id: 本节点 id，用于从 state 取上游结果
        :param runtime: 运行时注入（如 llm、retrievers、tools、db 等）
        :return: 本节点输出，执行器会合并到 state[node_id]
        """
        pass

    def _get_input(self, state: dict[str, Any], node_id: str, port: str = "input", default: Any = None) -> Any:
        """从 state 中按上游连线约定取输入。执行器可把上游节点输出放在 state[source_node_id]，本节点通过边知道 source。"""
        # 简化：若执行器已把「本节点输入」整理好，可在 state["_inputs"].get(node_id) 或 state[source_id]
        return state.get(port, default)
