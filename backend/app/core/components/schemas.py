"""组件 Schema：供前端与校验使用的输入/输出/配置定义"""
from typing import Any

from pydantic import BaseModel, Field


class PortDef(BaseModel):
    """单个输入或输出端口定义"""
    name: str = Field(..., description="端口名，用于连线与 state 读写")
    type: str = Field(default="any", description="类型：string|number|boolean|messages|message|object|any")
    required: bool = Field(default=False, description="是否必填")
    default: Any = Field(default=None, description="默认值")
    description: str = Field(default="", description="说明")


class ConfigFieldDef(BaseModel):
    """节点配置项定义"""
    name: str = Field(..., description="配置键名")
    type: str = Field(default="string", description="string|number|boolean|object|array|code")
    required: bool = Field(default=False)
    default: Any = None
    description: str = ""
    options: list[dict[str, Any]] | None = Field(default=None, description="枚举选项 [{label, value}]")


class ComponentSchema(BaseModel):
    """单个组件的完整 Schema（供注册与 API 返回）"""
    type_id: str = Field(..., description="组件唯一类型 id，与节点 type 一致")
    name: str = Field(..., description="显示名称")
    category: str = Field(
        default="basic",
        description="分类：llm|rag|agent|tool|logic|code|io|basic",
    )
    description: str = Field(default="", description="组件说明")
    input_ports: list[PortDef] = Field(default_factory=list, alias="input_schema")
    output_ports: list[PortDef] = Field(default_factory=list, alias="output_schema")
    config_schema: list[ConfigFieldDef] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def input_schema(self) -> list[PortDef]:
        return self.input_ports

    @property
    def output_schema(self) -> list[PortDef]:
        return self.output_ports
