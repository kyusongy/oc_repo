import pytest
from backend.tools.check_system import CheckSystemTool


@pytest.mark.asyncio
async def test_check_system_returns_os():
    tool = CheckSystemTool()
    result = await tool.execute({})
    assert result.success is True
    assert "os" in result.output
    assert "darwin" in result.output.lower()


@pytest.mark.asyncio
async def test_check_system_detects_git():
    tool = CheckSystemTool()
    result = await tool.execute({})
    assert "git" in result.output.lower()


@pytest.mark.asyncio
async def test_check_system_schema():
    tool = CheckSystemTool()
    schema = tool.to_schema()
    assert schema["function"]["name"] == "check_system"
    assert schema["function"]["parameters"]["properties"] == {}
