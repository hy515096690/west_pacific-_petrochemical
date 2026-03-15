#!/usr/bin/env python3
"""
可执行脚本：运行「用户输入 -> 大模型回复」测试工作流。

依赖：需已安装 langchain-openai、langchain-core（项目根 pip install -e . 或 backend 的依赖）。

用法：
  # 在 backend 目录下（推荐）
  cd backend
  set OPENAI_API_KEY=sk-xxx
  python scripts/run_workflow_user_llm.py
  python scripts/run_workflow_user_llm.py --message "你好，介绍一下你自己"

  # 在项目根目录下
  python backend/scripts/run_workflow_user_llm.py --message "你好"
"""
import argparse
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
            "name": "gpt-5.2",
            "config": {
                "model_name": os.environ.get("WORKFLOW_MODEL", "gpt-5.2"),
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


def main():
    parser = argparse.ArgumentParser(description="运行测试工作流：用户输入 -> 大模型回复")
    parser.add_argument("--message", "-m", default="你好，请用一句话介绍你自己。", help="用户输入内容")
    # parser.add_argument("--api-key", default=os.environ.get("WORKFLOW_TEST_API_KEY") or os.environ.get("OPENAI_API_KEY"), help="API Key")
    # parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"), help="API Base URL（可选）")
    parser.add_argument("--api-key", default="sk-piwdGQDA5K3hLYW_POzGx7_YKniTqEilSrQ0CjySBMx8L_IbYMgjvHdpfeU", help="API Key")
    parser.add_argument("--base-url", default="https://api.htzl.com.cn:30000/v1", help="API Base URL（可选）")
    args = parser.parse_args()

    if not args.api_key:
        print("请设置 OPENAI_API_KEY 或使用 --api-key 传入。", file=sys.stderr)
        sys.exit(1)

    inputs = {"messages": [{"role": "user", "content": args.message}]}
    runtime = {"api_key": args.api_key}
    if args.base_url:
        runtime["base_url"] = args.base_url.rstrip("/")

    print("工作流运行中：用户输入 -> 大模型回复")
    print("输入:", args.message)
    print("-" * 40)

    state = run_graph(GRAPH, inputs, runtime=runtime)

    if "error" in state.get("n_llm", {}):
        print("错误:", state["n_llm"]["error"], file=sys.stderr)
        sys.exit(2)

    reply = state.get("n_llm", {}).get("text", "")
    print("回复:", reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
