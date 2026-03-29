import pytest
from backend.tools.base import Tool, ToolResult, ToolRegistry


def test_tool_result_success():
    result = ToolResult(output="done", success=True)
    assert result.output == "done"
    assert result.success is True
    assert result.ui_payload is None


def test_tool_result_with_payload():
    result = ToolResult(output="data", success=True, ui_payload={"key": "val"})
    assert result.ui_payload == {"key": "val"}


class DummyTool(Tool):
    name = "dummy"
    description = "A test tool"
    parameters = {"type": "object", "properties": {"x": {"type": "string"}}}
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(output=f"got {params['x']}", success=True)


@pytest.mark.asyncio
async def test_tool_execute():
    tool = DummyTool()
    result = await tool.execute({"x": "hello"})
    assert result.output == "got hello"
    assert result.success is True


def test_tool_schema():
    tool = DummyTool()
    schema = tool.to_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "dummy"
    assert schema["function"]["description"] == "A test tool"
    assert schema["function"]["parameters"] == tool.parameters


def test_registry_get():
    tool = DummyTool()
    registry = ToolRegistry([tool])
    assert registry.get("dummy") is tool


def test_registry_get_missing():
    registry = ToolRegistry([])
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_registry_schemas():
    tool = DummyTool()
    registry = ToolRegistry([tool])
    schemas = registry.schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "dummy"
