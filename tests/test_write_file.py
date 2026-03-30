import pytest
from backend.tools.write_file import WriteFileTool


@pytest.mark.asyncio
async def test_write_file_in_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = WriteFileTool()
    result = await tool.execute(
        {
            "path": str(tmp_path / "test.txt"),
            "content": "hello world",
            "description": "test file",
        }
    )
    assert result.success is True
    assert (tmp_path / "test.txt").read_text() == "hello world"


@pytest.mark.asyncio
async def test_write_file_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = WriteFileTool()
    result = await tool.execute(
        {
            "path": str(tmp_path / "sub" / "dir" / "file.txt"),
            "content": "nested",
            "description": "nested file",
        }
    )
    assert result.success is True
    assert (tmp_path / "sub" / "dir" / "file.txt").read_text() == "nested"


@pytest.mark.asyncio
async def test_write_file_blocks_outside_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path / "workspace"))
    (tmp_path / "workspace").mkdir()
    tool = WriteFileTool()
    result = await tool.execute(
        {
            "path": "/tmp/evil_file.txt",
            "content": "hacked",
            "description": "bad file",
        }
    )
    assert result.success is False
    assert "Blocked" in result.output


@pytest.mark.asyncio
async def test_write_file_blocks_traversal(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("OC_WORKSPACE", str(workspace))
    tool = WriteFileTool()
    result = await tool.execute(
        {
            "path": str(workspace / ".." / "outside.txt"),
            "content": "escaped",
            "description": "traversal",
        }
    )
    assert result.success is False
    assert "Blocked" in result.output
