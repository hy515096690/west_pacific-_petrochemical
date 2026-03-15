"""ReAct 智能体节点：使用 LangGraph create_react_agent 或 LangChain Agent"""
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.workflow.nodes.base_node import BaseNode
from app.core.workflow.nodes.llm_node import _get_llm


def _get_tools_list(config: dict[str, Any], runtime: dict[str, Any] | None) -> list:
    """从 runtime.tools 按 tool_keys 取出工具列表。"""
    keys = config.get("tool_keys") or config.get("tools") or []
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(",") if k.strip()]
    tools_map = (runtime or {}).get("tools") or {}
    out = []
    for k in keys:
        if isinstance(tools_map, dict) and k in tools_map:
            out.append(tools_map[k])
        elif isinstance(tools_map, list):
            for t in tools_map:
                if getattr(t, "name", None) == k:
                    out.append(t)
                    break
    return out


def _run_react_agent(
    message: str,
    config: dict[str, Any],
    runtime: dict[str, Any] | None,
) -> dict[str, Any]:
    """使用 LangGraph prebuilt create_react_agent 运行 ReAct 智能体。"""
    try:
        from langgraph.prebuilt import create_react_agent
    except ImportError:
        return _run_react_agent_fallback(message, config, runtime)

    llm = _get_llm(config, runtime)
    tools = _get_tools_list(config, runtime)
    if not tools:
        # 无工具时退化为单次 LLM 调用
        response = llm.invoke([HumanMessage(content=message)])
        text = response.content if hasattr(response, "content") else str(response)
        return {"message": {"role": "assistant", "content": text}, "text": text, "intermediate_steps": []}

    graph = create_react_agent(llm, tools)
    max_iterations = int(config.get("max_iterations", 10))
    result = graph.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"recursion_limit": max_iterations},
    )
    messages = result.get("messages") or []
    last_content = ""
    for m in reversed(messages):
        if hasattr(m, "content") and m.content:
            last_content = m.content
            break
    return {
        "message": {"role": "assistant", "content": last_content},
        "text": last_content,
        "intermediate_steps": result.get("intermediate_steps", []),
    }


def _run_react_agent_fallback(
    message: str,
    config: dict[str, Any],
    runtime: dict[str, Any] | None,
) -> dict[str, Any]:
    """无 LangGraph prebuilt 时：仅用 LLM 单轮回复（无工具调用）。"""
    llm = _get_llm(config, runtime)
    response = llm.invoke([HumanMessage(content=message)])
    text = response.content if hasattr(response, "content") else str(response)
    return {"message": {"role": "assistant", "content": text}, "text": text, "intermediate_steps": []}


class AgentNode(BaseNode):
    type_id = "agent"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        upstream_output = state.get("_upstream_output") or {}
        message = (
            upstream_output.get("message")
            or upstream_output.get("text")
            or (state.get("_input") or {}).get("message")
            or (state.get("_input") or {}).get("text")
            or (state.get("_input") or {}).get("query")
        )
        if isinstance(message, dict):
            message = message.get("content") or message.get("text") or str(message)
        if not message:
            message = ""
        return _run_react_agent(message, config, runtime)
