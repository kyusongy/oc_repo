import json
import pytest
from backend.tools.list_files import ListFilesTool


@pytest.mark.asyncio
async def test_list_files_basic(tmp_repo, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_repo))
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo)})
    assert result.success is True
    files = json.loads(result.output)
    names = [f.rsplit("/", 1)[-1] for f in files]
    assert "README.md" in names
    assert "package.json" in names


@pytest.mark.asyncio
async def test_list_files_with_pattern(tmp_repo, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_repo))
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo), "pattern": "*.md"})
    files = json.loads(result.output)
    assert len(files) == 1
    assert files[0].endswith("README.md")


@pytest.mark.asyncio
async def test_list_files_nonexistent(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_path / "nonexistent")})
    assert result.success is False


@pytest.mark.asyncio
async def test_list_files_blocks_outside_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path / "workspace"))
    (tmp_path / "workspace").mkdir()
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_path)})
    assert result.success is False
    assert "Blocked" in result.output
