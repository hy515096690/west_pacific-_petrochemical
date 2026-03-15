"""RAG 节点：使用 LangChain Retriever 做知识库检索"""
from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.core.workflow.nodes.base_node import BaseNode


def _get_retriever(config: dict[str, Any], runtime: dict[str, Any] | None) -> BaseRetriever | None:
    key = config.get("retriever_key") or config.get("retriever")
    if not key:
        return None
    retrievers = (runtime or {}).get("retrievers") or {}
    return retrievers.get(key) if isinstance(retrievers, dict) else None


def _get_query(state: dict[str, Any], upstream_output: dict[str, Any]) -> str:
    q = (upstream_output or {}).get("query") or (upstream_output or {}).get("text")
    if q:
        return q
    inp = state.get("_input") or {}
    return inp.get("query") or inp.get("text") or inp.get("message") or ""


class RAGNode(BaseNode):
    type_id = "rag"

    def run(
        self,
        config: dict[str, Any],
        state: dict[str, Any],
        *,
        node_id: str = "",
        runtime: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        upstream_output = state.get("_upstream_output") or {}
        query = _get_query(state, upstream_output)
        if not query:
            return {"documents": [], "context": ""}

        retriever = _get_retriever(config, runtime)
        if retriever is None:
            return {"documents": [], "context": ""}

        top_k = int(config.get("top_k", 5))
        docs = retriever.invoke(query)
        if not isinstance(docs, list):
            docs = [docs] if docs else []
        docs = docs[:top_k]

        context = "\n\n".join(
            (d.page_content if isinstance(d, Document) else getattr(d, "page_content", str(d)))
            for d in docs
        )
        return {
            "documents": [
                {"page_content": d.page_content, "metadata": getattr(d, "metadata", {})}
                if isinstance(d, Document)
                else {"page_content": getattr(d, "page_content", str(d)), "metadata": getattr(d, "metadata", {})}
                for d in docs
            ],
            "context": context,
        }
