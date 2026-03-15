#!/usr/bin/env python3
"""
可执行脚本：Human-in-the-Loop 测试工作流。

流程：第一步用户输入 -> 第二步大模型回复 -> 第三步用户再输入 -> 第四步大模型回复。
用户两次输入均在控制台进行。

用法：
  cd backend
  set OPENAI_API_KEY=sk-xxx
  python scripts/run_workflow_user_llm.py

  # 指定 API 地址（可选）
  set OPENAI_BASE_URL=https://api.xxx.com/v1
  python scripts/run_workflow_user_llm.py
"""
import os
import sys

# 保证 backend 为运行根，可找到 app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.workflow.executor import run_graph

GRAPH = {
    "nodes": [
        {"id": "n_start", "type": "start", "name": "开始"},
        {
            "id": "n_llm",
            "type": "llm",
            "name": "大模型",
            "config": {
                "model_name": os.environ.get("WORKFLOW_MODEL", "gpt-3.5-turbo"),
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


def run_one_round(messages: list[dict], runtime: dict) -> str:
    """执行一轮：用当前 messages 跑图，返回大模型回复文本。"""
    state = run_graph(GRAPH, {"messages": messages}, runtime=runtime)
    if "error" in state.get("n_llm", {}):
        raise RuntimeError(state["n_llm"]["error"])
    return (state.get("n_llm") or {}).get("text", "")


def main():
    api_key = "sk-piwdGQDA5K3hLYW_POzGx7_YKniTqEilSrQ0CjySBMx8L_IbYMgjvHdpfeU"
    base_url = "https://api.htzl.com.cn:30000/v1"
    if not api_key:
        print("请设置环境变量 OPENAI_API_KEY 或 WORKFLOW_TEST_API_KEY。", file=sys.stderr)
        sys.exit(1)

    runtime = {"api_key": api_key}
    if base_url:
        runtime["base_url"] = base_url.rstrip("/")

    messages: list[dict] = []

    print("=== Human-in-the-Loop：两轮对话（控制台输入）===\n")

    # 第一步：用户输入
    try:
        user1 = input("【第一步】请输入：").strip() or "你好"
    except EOFError:
        user1 = "你好"
    messages.append({"role": "user", "content": user1})
    messages.append({"role": "system", "content": "[角色]你是一名沈阳市旅游助手。"})
    print("messages: ", messages)
    print()

    # 第二步：大模型回复
    print("【第二步】大模型回复中...")
    reply1 = run_one_round(messages, runtime)
    print("回复：", reply1)
    messages.append({"role": "assistant", "content": reply1})
    print("messages: ", messages)
    print()

    # 第三步：用户根据大模型结果再输入
    try:
        user2 = input("【第三步】请根据上文再输入：").strip() or "谢谢"
    except EOFError:
        user2 = "谢谢"
    messages.append({"role": "user", "content": user2})
    print("messages: ", messages)
    print()

    # 第四步：大模型再次回复
    print("【第四步】大模型回复中...")
    reply2 = run_one_round(messages, runtime)
    print("messages: ", messages)
    print("回复：", reply2)

    print("\n=== 两轮对话结束 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
