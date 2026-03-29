import pytest
from backend.tools.run_command import RunCommandTool


@pytest.mark.asyncio
async def test_run_command_success(tmp_path):
    tool = RunCommandTool()
    result = await tool.execute(
        {
            "command": "echo hello world",
            "description": "Print hello world",
            "cwd": str(tmp_path),
        }
    )
    assert result.success is True
    assert "hello world" in result.output


@pytest.mark.asyncio
async def test_run_command_failure(tmp_path):
    tool = RunCommandTool()
    result = await tool.execute(
        {
            "command": "ls /nonexistent_dir_12345",
            "description": "List a nonexistent directory",
            "cwd": str(tmp_path),
        }
    )
    assert result.success is False
    assert result.ui_payload["exit_code"] != 0


@pytest.mark.asyncio
async def test_run_command_timeout(tmp_path):
    tool = RunCommandTool()
    result = await tool.execute(
        {
            "command": "sleep 10",
            "description": "Sleep for 10 seconds",
            "cwd": str(tmp_path),
            "timeout": 1,
        }
    )
    assert result.success is False
    assert result.ui_payload["timed_out"] is True


@pytest.mark.asyncio
async def test_run_command_cwd(tmp_path):
    (tmp_path / "testfile.txt").write_text("hi")
    tool = RunCommandTool()
    result = await tool.execute(
        {
            "command": "ls testfile.txt",
            "description": "List testfile in cwd",
            "cwd": str(tmp_path),
        }
    )
    assert result.success is True
    assert "testfile.txt" in result.output


@pytest.mark.asyncio
async def test_run_command_schema():
    tool = RunCommandTool()
    schema = tool.to_schema()
    props = schema["function"]["parameters"]["properties"]
    assert "command" in props
    assert "description" in props
    assert "cwd" in props
    assert tool.requires_approval is True
