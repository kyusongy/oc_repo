from dataclasses import dataclass, asdict
import asyncio
import json
import os


def _workspace() -> str:
    return os.environ.get("OC_WORKSPACE", os.path.expanduser("~/oc_repo_workspace"))


def _projects_file() -> str:
    return os.path.join(_workspace(), "projects.json")


@dataclass
class ProjectInfo:
    name: str
    url: str
    path: str
    ports: list[int]
    installed_at: str
    status: str = "running"  # "running" | "stopped"
    launch_url: str | None = None


def load_projects() -> list[ProjectInfo]:
    path = _projects_file()
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return [ProjectInfo(**p) for p in data]


def save_projects(projects: list[ProjectInfo]):
    path = _projects_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump([asdict(p) for p in projects], f, indent=2)
    os.replace(tmp, path)


def add_project(info: ProjectInfo):
    projects = load_projects()
    # Update existing or append
    projects = [p for p in projects if p.name != info.name]
    projects.append(info)
    save_projects(projects)


def remove_project(name: str):
    projects = load_projects()
    projects = [p for p in projects if p.name != name]
    save_projects(projects)


def get_project(name: str) -> ProjectInfo | None:
    for p in load_projects():
        if p.name == name:
            return p
    return None


async def check_port_active(port: int) -> bool:
    proc = await asyncio.create_subprocess_shell(
        f"lsof -ti:{port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return bool(stdout.strip())


async def refresh_statuses(projects: list[ProjectInfo]) -> list[ProjectInfo]:
    for p in projects:
        if p.ports:
            active = any([await check_port_active(port) for port in p.ports])
            p.status = "running" if active else "stopped"
        else:
            p.status = "stopped"
    return projects
