import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kompas_eai.tools.registry import ToolContext, ToolError, ToolRegistry, count, mm


def make() -> ToolRegistry:
    r = ToolRegistry()

    @r.tool("echo_size", "Возвращает размер и количество (для теста).",
            {"type": "object",
             "properties": {"size": mm("Размер"), "n": count("Количество", default=1)},
             "required": ["size"], "additionalProperties": False}, mutates=False)
    def echo_size(ctx, size, n):
        return {"size": size, "n": n}

    @r.tool("always_fails", "Всегда ожидаемая ошибка.",
            {"type": "object", "properties": {}, "additionalProperties": False})
    def always_fails(ctx):
        raise ToolError("Нет открытой детали, сначала вызовите new_part", "no_part")

    @r.tool("crashes", "Всегда неожиданное исключение.",
            {"type": "object", "properties": {}, "additionalProperties": False})
    def crashes(ctx):
        raise RuntimeError("COM упал")

    return r


def test_ok_and_defaults():
    out = make().call("echo_size", {"size": 50}, ToolContext())
    assert out == {"ok": True, "tool": "echo_size", "result": {"size": 50, "n": 1}}


def test_json_string_arguments():
    out = make().call("echo_size", '{"size": 12.5, "n": 3}', ToolContext())
    assert out["ok"] and out["result"]["n"] == 3


def test_validation_errors():
    r, ctx = make(), ToolContext()
    e = r.call("echo_size", {}, ctx)["error"]
    assert e["code"] == "invalid_arguments" and "size" in e["message"]
    assert "больше 0" in r.call("echo_size", {"size": -5}, ctx)["error"]["message"]
    assert "больше максимума" in r.call("echo_size", {"size": 1e9}, ctx)["error"]["message"]
    assert "неизвестные" in r.call("echo_size", {"size": 1, "x": 2}, ctx)["error"]["message"]
    assert not r.call("echo_size", {"size": "10"}, ctx)["ok"]
    assert not r.call("echo_size", {"size": 10, "n": 2.5}, ctx)["ok"]


def test_unknown_tool_lists_available():
    e = make().call("drop_database", {}, ToolContext())["error"]
    assert e["code"] == "unknown_tool" and "echo_size" in e["message"]


def test_tool_error_and_crash():
    r, ctx = make(), ToolContext()
    assert r.call("always_fails", {}, ctx)["error"]["code"] == "no_part"
    e = r.call("crashes", {}, ctx)["error"]
    assert e["code"] == "internal_error" and "COM упал" in e["message"]


def test_schemas_export():
    r = make()
    a = r.schemas("anthropic")
    o = r.schemas("openai")
    assert {s["name"] for s in a} == set(r.names())
    assert o[0]["type"] == "function" and "parameters" in o[0]["function"]


def test_bad_registration():
    r = ToolRegistry()
    base = {"type": "object", "properties": {"a": {"type": "number", "description": "x"}},
            "additionalProperties": False}
    for bad in (
        {"type": "object", "properties": {}},                                   # нет additionalProperties
        {"type": "object", "properties": {"a": {"type": "number"}}, "additionalProperties": False},  # нет description
        {**base, "required": ["zzz"]},                                          # required вне properties
    ):
        try:
            r.tool("bad_tool", "d", bad)(lambda ctx: {})
        except ValueError:
            continue
        raise AssertionError(f"схема должна была отклониться: {bad}")
    r.tool("good_tool", "d", base)(lambda ctx, a=0: {})
    try:
        r.tool("good_tool", "d", base)(lambda ctx, a=0: {})
    except ValueError:
        pass
    else:
        raise AssertionError("дубликат имени должен отклоняться")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("OK ", name)
    print("test_registry: всё прошло")