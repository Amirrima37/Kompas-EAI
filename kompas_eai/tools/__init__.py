"""Слой инструментов агента. Реестр импортируется без КОМПАС;
load_all() подключает примитивы (а через них и kompas_eai.bridge)."""
from .registry import (  # noqa: F401
    ToolContext, ToolError, ToolRegistry, ToolSpec, registry, tool,
    mm, angle_deg, count, plane,
)


def load_all() -> None:
    """Регистрирует все инструменты. Вызывать один раз при старте агента."""
    from . import primitives  # noqa: F401