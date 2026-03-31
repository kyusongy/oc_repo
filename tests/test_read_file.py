import pytest
from backend.tools.read_file import ReadFileTool


@pytest.mark.asyncio
async def test_read_file_basic(tmp_repo, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_repo))
    tool = ReadFileTool()
    result = await tool.execute({"path": str(tmp_repo / "README.md")})
    assert result.success is True
    assert "# Test Project" in result.output


@pytest.mark.asyncio
async def test_read_file_max_lines(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    f = tmp_path / "big.txt"
    f.write_text("\n".join(f"line {i}" for i in range(100)))
    tool = ReadFileTool()
    result = await tool.execute({"path": str(f), "max_lines": 5})
    assert result.success is True
    assert "line 4" in result.output
    assert "line 5" not in result.output
    assert "truncated" in result.output.lower() or result.ui_payload


@pytest.mark.asyncio
async def test_read_file_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = ReadFileTool()
    result = await tool.execute({"path": str(tmp_path / "nonexistent.txt")})
    assert result.success is False


@pytest.mark.asyncio
async def test_read_file_blocks_outside_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path / "workspace"))
    (tmp_path / "workspace").mkdir()
    (tmp_path / "secret.txt").write_text("password123")
    tool = ReadFileTool()
    result = await tool.execute({"path": str(tmp_path / "secret.txt")})
    assert result.success is False
    assert "Blocked" in result.output
