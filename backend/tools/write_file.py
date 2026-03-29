import os

from backend.tools.base import Tool, ToolResult


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Write content to a file. Use this instead of shell commands (cat, echo) "
        "for creating configuration files, .env files, or any text file. "
        "This is safer and handles special characters correctly."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
            "description": {
                "type": "string",
                "description": "Plain-English explanation of what this file is for (shown to user)",
            },
        },
        "required": ["path", "content", "description"],
    }
    requires_approval = False  # Safe — just writes a file, no shell

    async def execute(self, params: dict) -> ToolResult:
        path = params["path"]
        content = params["content"]

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            return ToolResult(
                output=f"File written: {path}",
                success=True,
            )
        except Exception as e:
            return ToolResult(output=f"Error writing file: {e}", success=False)
