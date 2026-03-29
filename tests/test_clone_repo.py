import os
import pytest
from backend.tools.clone_repo import CloneRepoTool

WORKSPACE = os.path.expanduser("~/oc_repo_workspace")


@pytest.mark.asyncio
async def test_clone_repo_valid(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = CloneRepoTool()
    result = await tool.execute({"url": "https://github.com/octocat/Hello-World.git"})
    assert result.success is True
    assert "Hello-World" in result.output
    cloned_path = tmp_path / "Hello-World"
    assert cloned_path.exists()
    assert (cloned_path / ".git").exists()


@pytest.mark.asyncio
async def test_clone_repo_invalid_url(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = CloneRepoTool()
    result = await tool.execute(
        {"url": "https://github.com/not-a-real-user/not-a-real-repo-12345.git"}
    )
    assert result.success is False
    assert "error" in result.output.lower() or "fatal" in result.output.lower()


@pytest.mark.asyncio
async def test_clone_repo_schema():
    tool = CloneRepoTool()
    schema = tool.to_schema()
    assert schema["function"]["name"] == "clone_repo"
    assert "url" in schema["function"]["parameters"]["properties"]
