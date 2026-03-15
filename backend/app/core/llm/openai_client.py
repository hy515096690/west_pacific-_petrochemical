"""OpenAI 协议兼容的 HTTP 客户端：按 api_host + api_key 调用 /v1/chat/completions"""
from typing import Any, AsyncIterator

import httpx


def _normalize_api_host(host: str | None) -> str:
    if not host or not host.strip():
        return ""
    return host.strip().rstrip("/")


def _build_request_body(
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stream: bool = False,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict[str, float] | None = None,
    user: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """拼装 OpenAI 风格请求体，只包含非 None 字段。"""
    body: dict[str, Any] = {"model": model, "messages": messages, "stream": stream}
    if temperature is not None:
        body["temperature"] = temperature
    if top_p is not None:
        body["top_p"] = top_p
    if n is not None:
        body["n"] = n
    if stop is not None:
        body["stop"] = stop
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if presence_penalty is not None:
        body["presence_penalty"] = presence_penalty
    if frequency_penalty is not None:
        body["frequency_penalty"] = frequency_penalty
    if logit_bias is not None:
        body["logit_bias"] = logit_bias
    if user is not None:
        body["user"] = user
    for k, v in extra.items():
        if v is not None and k not in body:
            body[k] = v
    return body


def _common_kwargs(
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stream: bool = False,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict[str, float] | None = None,
    user: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """拼装请求体与 URL、headers 的公共参数，供 _json 与 _stream 使用。"""
    return _build_request_body(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
        stop=stop,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        **extra,
    )


async def chat_completion(
    base_url: str,
    api_key: str | None,
    *,
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stream: bool = False,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict[str, float] | None = None,
    user: str | None = None,
    **extra: Any,
) -> dict[str, Any] | AsyncIterator[str]:
    """
    调用 OpenAI 兼容的 /v1/chat/completions。
    stream=False 时返回 dict；stream=True 时返回异步迭代器（SSE 行），不能与 return 混用，故分两路实现。
    """
    if stream:
        return _chat_completion_stream(
            base_url,
            api_key,
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            n=n,
            stop=stop,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            logit_bias=logit_bias,
            user=user,
            **extra,
        )
    return await _chat_completion_json(
        base_url,
        api_key,
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stop=stop,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        **extra,
    )


async def _chat_completion_json(
    base_url: str,
    api_key: str | None,
    *,
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict[str, float] | None = None,
    user: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """非流式：返回完整 JSON。"""
    url = f"{_normalize_api_host(base_url)}/v1/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = _common_kwargs(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=False,
        stop=stop,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        **extra,
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _chat_completion_stream(
    base_url: str,
    api_key: str | None,
    *,
    model: str,
    messages: list[dict],
    temperature: float | None = None,
    top_p: float | None = None,
    n: int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    presence_penalty: float | None = None,
    frequency_penalty: float | None = None,
    logit_bias: dict[str, float] | None = None,
    user: str | None = None,
    **extra: Any,
) -> AsyncIterator[str]:
    """流式：仅 yield，无 return 值，避免与异步生成器冲突。"""
    url = f"{_normalize_api_host(base_url)}/v1/chat/completions"
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = _common_kwargs(
        model=model,
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=True,
        stop=stop,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        user=user,
        **extra,
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=body, headers=headers) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield line
                elif line:
                    yield line + "\n"
