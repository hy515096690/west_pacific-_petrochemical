"""开始节点：将工作流输入写入 state，供下游使用"""
from typing import Any

from app.core.workflow.nodes.base_node import BaseNode


class StartNode(BaseNode):
    type_id = "start"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 执行器应把用户输入放在 state["_input"]；本节点直接透传为输出
        input_data = state.get("_input", {})
        return {"input": input_data}
