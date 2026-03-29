import asyncio
import os

from backend.projects import _workspace
from backend.tools.base import Tool, ToolResult


def _repo_name(url: str) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name.removesuffix(".git")


class CloneRepoTool(Tool):
    name = "clone_repo"
    description = (
        "Clone a GitHub repository to the local workspace directory. "
        "Returns the path where the repo was cloned."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "GitHub repository URL (e.g., https://github.com/user/repo)",
            },
        },
        "required": ["url"],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        url = params["url"]
        repo_name = _repo_name(url)
        workspace = _workspace()
        os.makedirs(workspace, exist_ok=True)
        target = os.path.join(workspace, repo_name)

        if os.path.exists(target):
            return ToolResult(
                output=f"Repository already cloned at {target}",
                success=True,
            )

        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            url,
            target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            return ToolResult(
                output=f"Error cloning repo: {stderr.decode().strip()}",
                success=False,
            )

        return ToolResult(
            output=f"Cloned {url} to {target}",
            success=True,
        )
