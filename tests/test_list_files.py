import json
import pytest
from backend.tools.list_files import ListFilesTool


@pytest.mark.asyncio
async def test_list_files_basic(tmp_repo):
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo)})
    assert result.success is True
    files = json.loads(result.output)
    names = [f.rsplit("/", 1)[-1] for f in files]
    assert "README.md" in names
    assert "package.json" in names


@pytest.mark.asyncio
async def test_list_files_with_pattern(tmp_repo):
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo), "pattern": "*.md"})
    files = json.loads(result.output)
    assert len(files) == 1
    assert files[0].endswith("README.md")


@pytest.mark.asyncio
async def test_list_files_nonexistent():
    tool = ListFilesTool()
    result = await tool.execute({"path": "/nonexistent/path"})
    assert result.success is False
