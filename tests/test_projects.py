from backend.projects import (
    ProjectInfo,
    load_projects,
    add_project,
    remove_project,
    get_project,
)


def test_load_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    assert load_projects() == []


def test_add_and_load(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    info = ProjectInfo(
        name="test",
        url="https://github.com/test/test",
        path=str(tmp_path / "test"),
        ports=[3000],
        installed_at="2026-01-01T00:00:00Z",
    )
    add_project(info)
    projects = load_projects()
    assert len(projects) == 1
    assert projects[0].name == "test"


def test_add_replaces_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    info1 = ProjectInfo(
        name="test", url="url1", path="/p1", ports=[3000], installed_at="t1"
    )
    info2 = ProjectInfo(
        name="test", url="url2", path="/p2", ports=[4000], installed_at="t2"
    )
    add_project(info1)
    add_project(info2)
    projects = load_projects()
    assert len(projects) == 1
    assert projects[0].url == "url2"


def test_remove(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    add_project(ProjectInfo(name="a", url="", path="", ports=[], installed_at=""))
    add_project(ProjectInfo(name="b", url="", path="", ports=[], installed_at=""))
    remove_project("a")
    projects = load_projects()
    assert len(projects) == 1
    assert projects[0].name == "b"


def test_get_project(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    add_project(
        ProjectInfo(name="x", url="u", path="/p", ports=[8000], installed_at="t")
    )
    assert get_project("x") is not None
    assert get_project("y") is None
