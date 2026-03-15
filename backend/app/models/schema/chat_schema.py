"""OpenAI 兼容的 Chat Completions 请求/响应 Schema"""
from typing import Any

from pydantic import BaseModel, Field


# ---------- 请求（与 OpenAI API 对齐） ----------


class ChatMessage(BaseModel):
    role: str = Field(..., description="system | user | assistant")
    content: str = Field(..., description="消息内容")
    name: str | None = Field(None, description="可选，发送者名称")


class ChatCompletionRequest(BaseModel):
    """OpenAI 风格 /v1/chat/completions 请求体"""
    model: str = Field(..., description="模型 id 或 model_name，用于从 chat_model 表查 api_host/api_key")
    messages: list[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="采样温度")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="nucleus sampling")
    n: int | None = Field(1, ge=1, le=128, description="生成几条候选")
    stream: bool = Field(False, description="是否流式返回")
    stop: str | list[str] | None = Field(None, description="停止词")
    max_tokens: int | None = Field(None, ge=1, description="最大 token 数")
    presence_penalty: float | None = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0)
    logit_bias: dict[str, float] | None = Field(None, description="token 偏移")
    user: str | None = Field(None, description="终端用户标识，用于审计")
    # 部分兼容字段
    response_format: dict[str, Any] | None = Field(None, alias="response_format")
    seed: int | None = Field(None)
    tools: list[Any] | None = Field(None)
    tool_choice: str | dict[str, Any] | None = Field(None)
    store: bool | None = Field(None)

    class Config:
        populate_by_name = True
        extra = "allow"


# ---------- 响应（与 OpenAI API 对齐） ----------


class ChatChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str | None = None
    tool_calls: list[Any] | None = None


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: str | None = Field(None, description="stop | length | content_filter | null")


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI 风格 /v1/chat/completions 响应体"""
    id: str | None = None
    object: str = "chat.completion"
    created: int | None = None
    model: str = ""
    choices: list[ChatChoice] = []
    usage: Usage | None = None
    system_fingerprint: str | None = None

    class Config:
        extra = "allow"
