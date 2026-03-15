"""结束节点：将上游输出作为工作流最终输出"""
from typing import Any

from app.core.workflow.nodes.base_node import BaseNode


class EndNode(BaseNode):
    type_id = "end"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 上游输出通常在 state 中；执行器可约定把「指向 end 的节点」的输出 key 传入
        # 这里取 state["_upstream"] 或约定最后一个上游节点 id 在 runtime 中
        upstream = (runtime or {}).get("_upstream_output") or state.get("_upstream_output") or {}
        return {"output": upstream}
