"""LLM 节点：使用 LangChain ChatOpenAI 调用大模型"""
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.workflow.nodes.base_node import BaseNode


def _build_messages(
    state: dict[str, Any],
    config: dict[str, Any],
    upstream_output: dict[str, Any],
) -> list[BaseMessage]:
    """从上游输出或 state 拼装 messages（含 system）。"""
    messages: list[BaseMessage] = []
    system = (
        config.get("system_prompt")
        or (upstream_output or {}).get("system_prompt")
        or (state.get("_input") or {}).get("system_prompt")
    )
    if system:
        messages.append(SystemMessage(content=system))

    raw = (upstream_output or {}).get("messages") or (state.get("_input") or {}).get("messages")
    if isinstance(raw, list):
        for m in raw:
            if isinstance(m, dict):
                role = (m.get("role") or "user").lower()
                content = m.get("content") or m.get("text") or ""
                if role == "system":
                    messages.append(SystemMessage(content=content))
                elif role == "user" or role == "human":
                    messages.append(HumanMessage(content=content))
                elif role in ("assistant", "ai"):
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(HumanMessage(content=content))
            else:
                messages.append(m if isinstance(m, BaseMessage) else HumanMessage(content=str(m)))
    elif isinstance(raw, str):
        messages.append(HumanMessage(content=raw))
    elif not messages:
        # 无 messages 时用 _input.text 或 query
        inp = state.get("_input") or {}
        text = inp.get("text") or inp.get("query") or inp.get("message") or ""
        if text:
            messages.append(HumanMessage(content=text))

    return messages


def _get_llm(config: dict[str, Any], runtime: dict[str, Any] | None) -> ChatOpenAI:
    """从 runtime.llms 取或按 config 构造 ChatOpenAI。"""
    r = runtime or {}
    model_name = config.get("model_name") or config.get("model") or "gpt-3.5-turbo"
    llms = r.get("llms") or {}
    if isinstance(llms, dict) and model_name in llms:
        return llms[model_name]

    base_url = config.get("base_url") or r.get("base_url")
    api_key = config.get("api_key") or r.get("api_key") or ""
    return ChatOpenAI(
        model=model_name,
        openai_api_base=base_url or None,
        openai_api_key=api_key or "dummy",
        temperature=float(config.get("temperature", 0.7)),
        max_tokens=int(config.get("max_tokens", 2048)),
    )


class LLMNode(BaseNode):
    type_id = "llm"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 上游输出：执行器应把「指向本节点的上游」放在 state["_upstream_output"] 或按边取 state[source_id]
        upstream_output = state.get("_upstream_output") or {}
        if not upstream_output and node_id:
            for k, v in state.items():
                if k.startswith("_") or not isinstance(v, dict):
                    continue
                if "messages" in v or "text" in v:
                    upstream_output = v
                    break

        messages = _build_messages(state, config, upstream_output)
        if not messages:
            return {"message": None, "text": ""}

        llm = _get_llm(config, runtime)
        response = llm.invoke(messages)
        text = response.content if hasattr(response, "content") else str(response)
        return {
            "message": {"role": "assistant", "content": text},
            "text": text,
        }
