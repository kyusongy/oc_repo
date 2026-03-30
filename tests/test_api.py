import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_list_projects_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_list_projects_auto_detects(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    (tmp_path / "my-project").mkdir()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/projects")
        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "my-project"


@pytest.mark.asyncio
async def test_stop_project_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/projects/nonexistent/stop")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    project_dir = tmp_path / "deleteme"
    project_dir.mkdir()
    (project_dir / "file.txt").write_text("content")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete("/api/projects/deleteme")
        assert response.status_code == 200
        assert not project_dir.exists()


@pytest.mark.asyncio
async def test_history_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    project_dir = tmp_path / "myapp"
    project_dir.mkdir()
    messages = [{"kind": "user", "text": "hello"}, {"kind": "agent", "text": "hi"}]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Save
        response = await client.post(
            "/api/projects/myapp/history",
            json=messages,
        )
        assert response.status_code == 200
        # Load
        response = await client.get("/api/projects/myapp/history")
        assert response.status_code == 200
        assert response.json() == messages
