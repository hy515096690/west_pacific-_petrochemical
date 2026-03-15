"""条件分支节点：根据值或表达式选择出口（true/false）"""
from typing import Any

from app.core.workflow.nodes.base_node import BaseNode


def _eval_condition(value: Any, expression: str | None, state: dict[str, Any]) -> bool:
    """简单条件：无 expression 时看 value 布尔值；有 expression 时仅支持简单 key 查找。"""
    if expression:
        # 仅支持简单形式，如 "state.n1.text" 或 "input.key"；安全考虑不执行任意表达式
        expr = (expression or "").strip()
        if expr.startswith("state.") or expr.startswith("_"):
            parts = expr.replace("state.", "").split(".")
            cur = state
            for p in parts:
                cur = cur.get(p, {}) if isinstance(cur, dict) else None
                if cur is None:
                    return False
            return bool(cur)
        return bool(value)
    return bool(value)


class ConditionNode(BaseNode):
    type_id = "condition"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        upstream_output = state.get("_upstream_output") or {}
        value = upstream_output.get("value") or upstream_output.get("condition_result") or upstream_output.get("result")
        if value is None:
            value = state.get("_input") or upstream_output

        expression = config.get("expression")
        result = _eval_condition(value, expression, state)
        if isinstance(value, str) and value.lower() in ("true", "false", "yes", "no"):
            result = value.lower() in ("true", "yes")

        return {"true": value if result else None, "false": value if not result else None, "branch": "true" if result else "false"}
