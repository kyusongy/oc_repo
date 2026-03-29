import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.agent.engine import AgentEngine
from backend.tools.base import Tool, ToolResult, ToolRegistry


class EchoTool(Tool):
    name = "echo"
    description = "Echo back the input"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(output=f"echoed: {params['text']}", success=True)


def _make_text_response(text: str):
    choice = MagicMock()
    choice.message.content = text
    choice.message.tool_calls = None
    choice.finish_reason = "stop"
    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_response(tool_name: str, arguments: dict):
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)
    choice = MagicMock()
    choice.message.content = None
    choice.message.tool_calls = [tool_call]
    choice.finish_reason = "tool_calls"
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_engine_text_response():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _make_text_response("Hello!")

    registry = ToolRegistry([EchoTool()])
    engine = AgentEngine(mock_client, "test-model", registry)

    messages = []
    async for msg in engine.run("Hi", messages):
        assert msg == "Hello!"


@pytest.mark.asyncio
async def test_engine_tool_call_then_text():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        _make_tool_response("echo", {"text": "test"}),
        _make_text_response("I echoed: test"),
    ]

    registry = ToolRegistry([EchoTool()])
    engine = AgentEngine(mock_client, "test-model", registry)

    messages = []
    results = []
    async for msg in engine.run("Echo something", messages):
        results.append(msg)

    assert len(results) == 1
    assert "I echoed: test" in results[0]
