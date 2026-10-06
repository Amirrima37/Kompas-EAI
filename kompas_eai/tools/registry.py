"""Реестр инструментов ИИ-агента Kompas-EAI.

ИИ не исполняет произвольный код: он может только вызвать инструмент,
зарегистрированный здесь, с аргументами, прошедшими проверку по JSON-схеме.
Единицы: длины в мм, углы в градусах.
"""
from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from jsonschema import Draft202012Validator

log = logging.getLogger(__name__)

MAX_MM = 10_000.0
MAX_COUNT = 1000
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")

SchemaFormat = Literal["anthropic", "openai"]


# --------------------------------------------------------------------------
# Ошибки и контекст
# --------------------------------------------------------------------------
class ToolError(Exception):
    """Ожидаемая ошибка инструмента. Текст уйдёт ИИ как есть, пишите по-русски
    и конкретно: что не так и что можно сделать."""

    def __init__(self, message: str, code: str = "tool_error") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class ToolContext:
    """Состояние сессии, которое инструменты читают и меняют.

    Поля заполняет слой, который запускает агента (или сами инструменты,
    например new_part). Тип Any: КОМПАС-объекты — COM-обёртки.
    """
    app: Any = None
    doc: Any = None
    part: Any = None
    state: dict[str, Any] = field(default_factory=dict)


Handler = Callable[..., dict[str, Any]]


# --------------------------------------------------------------------------
# Хелперы для описания параметров (чтобы схемы были короткими и однотипными)
# --------------------------------------------------------------------------
def mm(description: str, *, minimum: float | None = None,
       exclusive_minimum: float | None = 0.0, maximum: float = MAX_MM,
       default: float | None = None) -> dict[str, Any]:
    """Длина в мм. По умолчанию строго > 0 и <= MAX_MM.
    Для смещений, которые могут быть отрицательными: minimum=-MAX_MM."""
    p: dict[str, Any] = {"type": "number", "description": f"{description}, мм",
                         "maximum": maximum}
    if minimum is not None:
        p["minimum"] = minimum
    elif exclusive_minimum is not None:
        p["exclusiveMinimum"] = exclusive_minimum
    if default is not None:
        p["default"] = default
    return p


def angle_deg(description: str, *, default: float | None = None) -> dict[str, Any]:
    p: dict[str, Any] = {"type": "number", "description": f"{description}, градусы",
                         "minimum": -360, "maximum": 360}
    if default is not None:
        p["default"] = default
    return p


def count(description: str, *, minimum: int = 1, maximum: int = MAX_COUNT,
          default: int | None = None) -> dict[str, Any]:
    p: dict[str, Any] = {"type": "integer", "description": description,
                         "minimum": minimum, "maximum": maximum}
    if default is not None:
        p["default"] = default
    return p


def plane(description: str = "Базовая плоскость эскиза", *,
          default: str = "XOY") -> dict[str, Any]:
    return {"type": "string", "enum": ["XOY", "XOZ", "YOZ"],
            "description": description, "default": default}


# --------------------------------------------------------------------------
# Описание инструмента
# --------------------------------------------------------------------------
def _check_schema(name: str, schema: dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise ValueError(f"{name}: схема параметров должна иметь type='object'")
    if schema.get("additionalProperties") is not False:
        raise ValueError(f"{name}: нужен 'additionalProperties': False "
                         "(иначе ИИ сможет передать лишнее)")
    Draft202012Validator.check_schema(schema)
    props = schema.get("properties", {})
    for pname, p in props.items():
        if not p.get("description"):
            raise ValueError(f"{name}: у параметра '{pname}' нет description")
    unknown = set(schema.get("required", [])) - set(props)
    if unknown:
        raise ValueError(f"{name}: required содержит неизвестные поля {sorted(unknown)}")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    mutates: bool = True  # меняет ли модель; False для измерений/чтения
    validator: Draft202012Validator = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not _NAME_RE.match(self.name):
            raise ValueError(f"Недопустимое имя инструмента: {self.name!r} "
                             "(snake_case, 3-64 символа, латиница)")
        if not self.description.strip():
            raise ValueError(f"{self.name}: пустое description")
        _check_schema(self.name, self.parameters)
        object.__setattr__(self, "validator", Draft202012Validator(self.parameters))


# --------------------------------------------------------------------------
# Сообщения об ошибках валидации по-русски
# --------------------------------------------------------------------------
def _ru_error(err) -> str:
    path = ".".join(str(p) for p in err.absolute_path)
    v, inst, sch = err.validator, err.instance, err.schema
    if v == "required":
        m = re.findall(r"'([^']+)'", err.message)
        return f"не хватает обязательного параметра '{m[0] if m else '?'}'"
    if v == "additionalProperties":
        names = re.findall(r"'([^']+)'", err.message)
        return f"неизвестные параметры: {', '.join(names)}"
    if v == "minimum":
        return f"'{path}': {inst} меньше минимума {sch['minimum']}"
    if v == "exclusiveMinimum":
        return f"'{path}': {inst} должно быть больше {sch['exclusiveMinimum']}"
    if v == "maximum":
        return f"'{path}': {inst} больше максимума {sch['maximum']}"
    if v == "type":
        return f"'{path}': ожидается {sch['type']}, получено {type(inst).__name__}"
    if v == "enum":
        return f"'{path}': {inst!r} не из допустимых {sch['enum']}"
    return f"'{path}': {err.message}" if path else err.message


def _fail(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, **extra}}


# --------------------------------------------------------------------------
# Реестр
# --------------------------------------------------------------------------
class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    # --- регистрация ------------------------------------------------------
    def register(self, spec: ToolSpec) -> ToolSpec:
        if spec.name in self._tools:
            raise ValueError(f"Инструмент {spec.name!r} уже зарегистрирован")
        self._tools[spec.name] = spec
        return spec

    def tool(self, name: str, description: str, parameters: dict[str, Any],
             *, mutates: bool = True) -> Callable[[Handler], Handler]:
        """Декоратор: @registry.tool("create_cylinder", "...", {...})
        Обработчик: def fn(ctx: ToolContext, **params) -> dict."""
        def deco(fn: Handler) -> Handler:
            self.register(ToolSpec(name, description, parameters, fn, mutates))
            return fn
        return deco

    # --- чтение -----------------------------------------------------------
    def names(self) -> list[str]:
        return sorted(self._tools)

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def schemas(self, fmt: SchemaFormat = "anthropic") -> list[dict[str, Any]]:
        """Описания инструментов в формате tool-calling провайдера."""
        out: list[dict[str, Any]] = []
        for s in self._tools.values():
            params = copy.deepcopy(s.parameters)
            if fmt == "anthropic":
                out.append({"name": s.name, "description": s.description,
                            "input_schema": params})
            elif fmt == "openai":
                out.append({"type": "function", "function": {
                    "name": s.name, "description": s.description,
                    "parameters": params}})
            else:
                raise ValueError(f"Неизвестный формат: {fmt!r}")
        return out

    # --- вызов ------------------------------------------------------------
    def call(self, name: str, arguments: dict[str, Any] | str | None,
             ctx: ToolContext) -> dict[str, Any]:
        """Единственная точка, через которую ИИ запускает инструменты.
        Не бросает исключений: всегда возвращает {"ok": ...}."""
        spec = self._tools.get(name)
        if spec is None:
            return _fail("unknown_tool",
                         f"Инструмента '{name}' нет. Доступны: {', '.join(self.names())}")

        if arguments is None:
            arguments = {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError as e:
                return _fail("bad_arguments", f"Аргументы не являются JSON: {e}")
        if not isinstance(arguments, dict):
            return _fail("bad_arguments", "Аргументы должны быть JSON-объектом")

        args = dict(arguments)
        for pname, p in spec.parameters.get("properties", {}).items():
            if pname not in args and "default" in p:
                args[pname] = p["default"]

        errors = sorted(spec.validator.iter_errors(args),
                        key=lambda e: [str(p) for p in e.absolute_path])
        if errors:
            msgs = [_ru_error(e) for e in errors]
            return _fail("invalid_arguments", "; ".join(msgs), details=msgs)

        log.info("tool %s %s", name, args)
        try:
            result = spec.handler(ctx, **args)
            if not isinstance(result, dict):
                raise TypeError(f"обработчик вернул {type(result).__name__}, нужен dict")
            json.dumps(result)  # результат должен сериализоваться для ИИ
        except ToolError as e:
            return _fail(e.code, e.message)
        except Exception as e:  # COM-ошибки и баги: в лог с traceback, ИИ получает суть
            log.exception("tool %s упал", name)
            return _fail("internal_error", f"{type(e).__name__}: {e}")
        return {"ok": True, "tool": name, "result": result}


# Глобальный реестр проекта: primitives.py регистрирует инструменты через @tool
registry = ToolRegistry()
tool = registry.tool