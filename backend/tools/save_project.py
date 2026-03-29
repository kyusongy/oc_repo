from datetime import datetime, timezone

from backend.projects import ProjectInfo, add_project
from backend.tools.base import Tool, ToolResult


class SaveProjectTool(Tool):
    name = "save_project"
    description = (
        "Save project metadata after a successful install and launch. "
        "Call this BEFORE reporting 'done' status so the user can manage the project later."
    )
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Project name (e.g., 'OpenLecture')",
            },
            "url": {
                "type": "string",
                "description": "GitHub repository URL",
            },
            "path": {
                "type": "string",
                "description": "Absolute path to the cloned project directory",
            },
            "ports": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of ports the project is running on",
            },
            "launch_url": {
                "type": "string",
                "description": "URL the user should open in their browser (e.g., http://localhost:5175)",
            },
        },
        "required": ["name", "url", "path", "ports"],
    }
    requires_approval = False

    def __init__(self):
        self.session = None  # Injected by engine

    async def execute(self, params: dict) -> ToolResult:
        info = ProjectInfo(
            name=params["name"],
            url=params["url"],
            path=params["path"],
            ports=params["ports"],
            installed_at=datetime.now(timezone.utc).isoformat(),
            status="running",
            launch_url=params.get("launch_url"),
        )
        add_project(info)

        # Notify frontend so it can show the success screen
        if self.session:
            from dataclasses import asdict

            await self.session.send(
                {
                    "type": "project_saved",
                    "project": asdict(info),
                }
            )

        return ToolResult(
            output=f"Project '{info.name}' saved. Ports: {info.ports}, URL: {info.launch_url}",
            success=True,
        )
