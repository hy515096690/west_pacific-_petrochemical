"""工作流执行器：支持两种执行方式

1. run_graph(graph_json, inputs, runtime)
   - 执行「我们定义的图」：nodes[{ id, type, config }] + edges[{ source, target }]
   - type 必须来自 NODE_REGISTRY（start/llm/rag/agent/tool/condition/code/end）
   - 适合低代码编排、可视化画布导出的 JSON

2. run_langgraph(compiled_graph, inputs, config?)
   - 执行「你用 LangChain/LangGraph 在代码里搭的图」
   - 传入已 compile 的 LangGraph 图，直接 invoke
   - 适合纯代码开发、任意 LangGraph StateGraph
"""
from collections import deque
from typing import Any

from app.core.workflow.nodes import NODE_REGISTRY, get_node


def _build_adjacency(nodes: list[dict], edges: list[dict]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """边列表 -> 入边、出边。edge: {source, target} 或 {source_node_id, target_node_id}"""
    in_edges: dict[str, list[str]] = {}
    out_edges: dict[str, list[str]] = {}
    node_ids = {n.get("id") for n in nodes if n.get("id")}
    for nid in node_ids:
        in_edges.setdefault(nid, [])
        out_edges.setdefault(nid, [])

    for e in edges or []:
        src = e.get("source") or e.get("source_node_id")
        tgt = e.get("target") or e.get("target_node_id")
        if not src or not tgt:
            continue
        if src in node_ids and tgt in node_ids:
            in_edges.setdefault(tgt, []).append(src)
            out_edges.setdefault(src, []).append(tgt)

    return in_edges, out_edges


def _topo_sort(node_ids: list[str], in_edges: dict[str, list[str]], out_edges: dict[str, list[str]]) -> list[str]:
    """标准 Kahn 拓扑排序。"""
    in_deg = {nid: len(in_edges.get(nid, [])) for nid in node_ids}
    q = deque(nid for nid in node_ids if in_deg[nid] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in out_edges.get(u, []):
            if v in in_deg:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    q.append(v)
    return order if len(order) == len(node_ids) else list(node_ids)


def run_graph(
    graph: dict[str, Any],
    inputs: dict[str, Any],
    *,
    runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    执行工作流图。
    :param graph: { nodes: [{ id, type, config?, name? }], edges: [{ source, target }] }
    :param inputs: 工作流输入，会放入 state["_input"]
    :param runtime: 注入的 llm、retrievers、tools 等
    :return: 最终 state，出口节点输出在对应 state[node_id]
    """
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    node_ids = [n["id"] for n in nodes if n.get("id")]
    in_edges, out_edges = _build_adjacency(nodes, edges)
    order = _topo_sort(node_ids, in_edges, out_edges)

    state: dict[str, Any] = {"_input": inputs, "_runtime": runtime or {}}
    runtime = runtime or {}

    for nid in order:
        node_def = next((n for n in nodes if n.get("id") == nid), None)
        if not node_def:
            continue
        node_type = node_def.get("type") or "start"
        config = node_def.get("config") or {}

        # 上游输出：若有多个上游，合并为一个 dict（按边约定可后续细化）
        preds = in_edges.get(nid, [])
        upstream_output: dict[str, Any] = {}
        if len(preds) == 1:
            upstream_output = state.get(preds[0]) or {}
        elif preds:
            for p in preds:
                upstream_output[f"from_{p}"] = state.get(p)

        state["_upstream_output"] = upstream_output

        node_runner = get_node(node_type)
        if not node_runner:
            state[nid] = {"error": f"unknown node type: {node_type}"}
            continue
        try:
            out = node_runner.run(config, state, node_id=nid, runtime=runtime)
            state[nid] = out
        except Exception as e:
            state[nid] = {"error": str(e)}
            raise

    return state


def run_langgraph(
    compiled_graph: Any,
    inputs: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    执行「用 LangChain/LangGraph 搭的图」：传入已编译的图，直接 invoke。

    适用：你在代码里用 StateGraph 等搭好的任意图，compile 后交给本函数执行。

    :param compiled_graph: LangGraph 的 compiled graph（有 .invoke 方法）
    :param inputs: 图的初始 state，例如 {"messages": [HumanMessage(...)]}
    :param config: 可选，传给 invoke 的 config（如 recursion_limit）
    :return: invoke 的完整返回（一般为最终 state）

    示例:
        from langgraph.graph import StateGraph, END
        def node_a(state): return {"x": state.get("x", 0) + 1}
        graph = StateGraph(dict).add_node("a", node_a).add_edge("a", END).set_entry_point("a")
        compiled = graph.compile()
        out = run_langgraph(compiled, {"x": 1})  # => {"x": 2, ...}
    """
    invoke_config = config or {}
    result = compiled_graph.invoke(inputs, config=invoke_config)
    return result if isinstance(result, dict) else {"result": result}
