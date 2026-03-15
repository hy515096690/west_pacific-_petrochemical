"""工具节点：调用单个 LangChain 工具"""
from typing import Any

from langchain_core.tools import BaseTool

from app.core.workflow.nodes.base_node import BaseNode


def _get_tool(config: dict[str, Any], runtime: dict[str, Any] | None) -> BaseTool | None:
    name = config.get("tool_name") or config.get("tool")
    if not name:
        return None
    tools = (runtime or {}).get("tools") or {}
    if isinstance(tools, dict):
        return tools.get(name)
    if isinstance(tools, list):
        for t in tools:
            if getattr(t, "name", None) == name:
                return t
    return None


class ToolNode(BaseNode):
    type_id = "tool"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        upstream_output = state.get("_upstream_output") or {}
        tool_input = upstream_output.get("tool_input") or upstream_output.get("input") or (state.get("_input") or {}).get("tool_input")
        if tool_input is None:
            tool_input = state.get("_input") or {}

        tool = _get_tool(config, runtime)
        if tool is None:
            return {"result": None, "error": "tool not found"}

        try:
            out = tool.invoke(tool_input)
        except Exception as e:
            return {"result": None, "error": str(e)}
        return {"result": out}
