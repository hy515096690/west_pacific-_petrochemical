"""Python 代码节点：执行用户提供的 main(state) -> dict（需在受控环境运行）"""
from typing import Any

from app.core.workflow.nodes.base_node import BaseNode


def _run_code_sandbox(code: str, state: dict[str, Any]) -> dict[str, Any]:
    """
    在受限环境中执行 code 中的 main(state) 并返回结果。
    当前为占位实现：仅支持极简白名单（无文件/网络）。生产环境建议使用 RestrictedPython 或子进程+超时。
    """
    try:
        import builtins
        safe_builtins = {
            "abs", "all", "any", "bool", "dict", "enumerate", "float", "int", "len",
            "list", "max", "min", "range", "round", "set", "sorted", "str", "sum",
            "tuple", "zip", "None", "True", "False", "isinstance", "getattr", "hasattr",
        }
        restricted = {k: getattr(builtins, k) for k in safe_builtins if hasattr(builtins, k)}
        restricted["__builtins__"] = restricted
        local: dict[str, Any] = {"state": state, "result": None}
        exec(code, restricted, local)
        main = local.get("main")
        if callable(main):
            out = main(state)
            return out if isinstance(out, dict) else {"result": out}
        return {"result": None}
    except Exception as e:
        return {"result": None, "error": str(e)}


class CodeNode(BaseNode):
    type_id = "code"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        code = config.get("code") or "def main(state): return {}"
        return _run_code_sandbox(code, state)
