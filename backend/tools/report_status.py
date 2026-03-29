from backend.tools.base import Tool, ToolResult


class ReportStatusTool(Tool):
    name = "report_status"
    description = (
        "Update the status indicator in the UI to show the current phase and progress. "
        "Use this to keep the user informed about what's happening."
    )
    parameters = {
        "type": "object",
        "properties": {
            "phase": {
                "type": "string",
                "enum": ["scanning", "installing", "launching", "done", "error"],
                "description": "Current phase of the installation process",
            },
            "message": {
                "type": "string",
                "description": "Human-readable status message",
            },
            "progress": {
                "type": "number",
                "description": "Progress percentage (0-100), omit if unknown",
            },
        },
        "required": ["phase", "message"],
    }
    requires_approval = False

    def __init__(self):
        self.session = None

    async def execute(self, params: dict) -> ToolResult:
        if not self.session:
            return ToolResult(output="Error: no session available", success=False)

        await self.session.send_status(
            phase=params["phase"],
            message=params["message"],
            progress=params.get("progress"),
        )
        return ToolResult(output="Status updated", success=True)
