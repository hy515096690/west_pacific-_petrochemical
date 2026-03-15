"""对话接口：OpenAI 协议兼容的 /chat/completions，模型配置从 chat_model 表读取"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.llm.openai_client import chat_completion
from app.models.schema.chat_schema import ChatCompletionRequest
from app.services.chat_model_service import get_chat_model, normalize_api_host

router = APIRouter(prefix="/chat", tags=["对话"])


def _messages_to_dicts(messages: list) -> list[dict]:
    return [m.model_dump(exclude_none=True) if hasattr(m, "model_dump") else m for m in messages]


@router.post("/completions")
async def chat_completions_api(
    body: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    User = Depends(get_current_user)
):
    """
    OpenAI 兼容的 /v1/chat/completions。
    body.model 为模型名称或 id（如 "gpt-4" 或表 chat_model 中的 model_name），
    接口会从 chat_model 表查 api_host、api_key 并请求对应上游。
    支持全部 OpenAI 请求参数：messages, temperature, top_p, n, stream, stop, max_tokens, presence_penalty, frequency_penalty, logit_bias, user 等。
    """
    # 支持通过 model 传 id（如 "1"）或 model_name
    model_id: int | None = None
    model_name: str | None = body.model
    if body.model.isdigit():
        model_id = int(body.model)
        model_name = None

    chat_model = await get_chat_model(db, model_id=model_id, model_name=model_name)
    if not chat_model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"未找到模型配置：model={body.model}，请在 chat_model 表中配置 api_host、api_key",
        )
    base_url = normalize_api_host(chat_model.api_host or "")
    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该模型未配置 api_host",
        )

    # 上游可能要求 model 为具体名称，用 DB 里的 model_name 或请求里的 model
    upstream_model = (chat_model.model_name or body.model).strip()
    messages = _messages_to_dicts(body.messages)
    extra = {}
    if body.response_format is not None:
        extra["response_format"] = body.response_format
    if body.seed is not None:
        extra["seed"] = body.seed
    if body.tools is not None:
        extra["tools"] = body.tools
    if body.tool_choice is not None:
        extra["tool_choice"] = body.tool_choice
    if body.store is not None:
        extra["store"] = body.store

    if body.stream:
        # chat_completion(..., stream=True) 是 async 函数，需 await 得到异步生成器后再迭代
        stream_iter = await chat_completion(
            base_url,
            chat_model.api_key,
            model=upstream_model,
            messages=messages,
            temperature=body.temperature,
            top_p=body.top_p,
            n=body.n,
            stream=True,
            stop=body.stop,
            max_tokens=body.max_tokens,
            presence_penalty=body.presence_penalty,
            frequency_penalty=body.frequency_penalty,
            logit_bias=body.logit_bias,
            user=body.user,
            **extra,
        )

        async def stream_gen():
            async for chunk in stream_iter:
                # SSE 规范：每个事件以双换行 \n\n 结束，便于客户端解析
                if not chunk.endswith("\n\n"):
                    chunk = chunk.rstrip("\n") + "\n\n"
                yield chunk

        return StreamingResponse(
            stream_gen(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    result = await chat_completion(
        base_url,
        chat_model.api_key,
        model=upstream_model,
        messages=messages,
        temperature=body.temperature,
        top_p=body.top_p,
        n=body.n,
        stream=False,
        stop=body.stop,
        max_tokens=body.max_tokens,
        presence_penalty=body.presence_penalty,
        frequency_penalty=body.frequency_penalty,
        logit_bias=body.logit_bias,
        user=body.user,
        **extra,
    )
    return JSONResponse(content=result)
