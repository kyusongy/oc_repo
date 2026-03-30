import json
import pytest
from backend.tools.save_project import SaveProjectTool


@pytest.mark.asyncio
async def test_save_project_writes_json(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = SaveProjectTool()
    tool.session = None  # no session = no WebSocket message
    result = await tool.execute(
        {
            "name": "test-project",
            "url": "https://github.com/test/test",
            "path": str(tmp_path / "test-project"),
            "ports": [3000, 8000],
            "launch_url": "http://localhost:3000",
        }
    )
    assert result.success is True
    assert "test-project" in result.output

    # Verify it's in projects.json
    projects_file = tmp_path / "projects.json"
    assert projects_file.exists()
    data = json.loads(projects_file.read_text())
    assert len(data) == 1
    assert data[0]["name"] == "test-project"
    assert data[0]["ports"] == [3000, 8000]
    assert data[0]["status"] == "running"


@pytest.mark.asyncio
async def test_save_project_schema():
    tool = SaveProjectTool()
    schema = tool.to_schema()
    assert schema["function"]["name"] == "save_project"
    props = schema["function"]["parameters"]["properties"]
    assert "name" in props
    assert "url" in props
    assert "ports" in props
