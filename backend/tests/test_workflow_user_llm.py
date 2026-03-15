"""测试工作流：用户输入 -> 大模型回复（可用 mock 或真实 API）"""
import os

import pytest

from app.core.workflow.executor import run_graph


# 图定义：start -> llm -> end
USER_LLM_GRAPH = {
    "nodes": [
        {"id": "n_start", "type": "start", "name": "开始"},
        {
            "id": "n_llm",
            "type": "llm",
            "name": "大模型",
            "config": {
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 512,
            },
        },
        {"id": "n_end", "type": "end", "name": "结束"},
    ],
    "edges": [
        {"source": "n_start", "target": "n_llm"},
        {"source": "n_llm", "target": "n_end"},
    ],
}


def test_workflow_user_llm_with_mock():
    """使用 mock LLM，不请求真实 API。"""
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessage
    from langchain_openai import ChatOpenAI

    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.invoke.return_value = AIMessage(content="你好，我是测试回复。")

    runtime = {"llms": {"gpt-3.5-turbo": mock_llm}}
    inputs = {
        "messages": [{"role": "user", "content": "请说你好"}],
    }

    state = run_graph(USER_LLM_GRAPH, inputs, runtime=runtime)

    assert "n_llm" in state
    assert state["n_llm"].get("text") == "你好，我是测试回复。"
    assert state["n_llm"].get("message", {}).get("content") == "你好，我是测试回复。"


def test_workflow_user_llm_input_as_text():
    """用户输入仅传 text 时，LLM 也能收到。"""
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessage
    from langchain_openai import ChatOpenAI

    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.invoke.return_value = AIMessage(content="收到：你好世界")

    runtime = {"llms": {"gpt-3.5-turbo": mock_llm}}
    inputs = {"text": "你好世界"}

    state = run_graph(USER_LLM_GRAPH, inputs, runtime=runtime)

    assert "n_llm" in state
    assert "收到" in state["n_llm"].get("text", "")


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") and not os.environ.get("WORKFLOW_TEST_API_KEY"),
    reason="需要 OPENAI_API_KEY 或 WORKFLOW_TEST_API_KEY 才请求真实 API",
)
def test_workflow_user_llm_real_api():
    """请求真实 OpenAI 兼容 API（需设置 OPENAI_API_KEY 或 WORKFLOW_TEST_API_KEY）。"""
    api_key = os.environ.get("WORKFLOW_TEST_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")  # 可选，兼容国内转发

    runtime = {"api_key": api_key}
    if base_url:
        runtime["base_url"] = base_url

    inputs = {"messages": [{"role": "user", "content": "只说一句话：你好"}]}
    state = run_graph(USER_LLM_GRAPH, inputs, runtime=runtime)

    assert "n_llm" in state
    assert "error" not in state["n_llm"]
    assert len((state["n_llm"].get("text") or "").strip()) > 0
