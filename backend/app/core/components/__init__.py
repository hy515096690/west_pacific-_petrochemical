"""组件层：Schema 与注册表，供工作流编排与 API 使用"""
from app.core.components.registry import (
    BUILTIN_COMPONENTS,
    get_component,
    list_components,
    get_registry,
    register_component,
)
from app.core.components.schemas import ComponentSchema, ConfigFieldDef, PortDef

__all__ = [
    "ComponentSchema",
    "ConfigFieldDef",
    "PortDef",
    "BUILTIN_COMPONENTS",
    "get_component",
    "list_components",
    "get_registry",
    "register_component",
]
