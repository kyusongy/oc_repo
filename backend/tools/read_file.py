import os

from backend.tools.base import Tool, ToolResult

DEFAULT_MAX_LINES = 200


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read the contents of a file. Use max_lines to limit output for large files. "
        "Defaults to 200 lines."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Absolute path to the file to read",
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to return (default 200)",
            },
        },
        "required": ["path"],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        path = params["path"]
        max_lines = params.get("max_lines", DEFAULT_MAX_LINES)

        if not os.path.isfile(path):
            return ToolResult(output=f"File not found: {path}", success=False)

        try:
            with open(path, "r", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return ToolResult(output=f"Error reading file: {e}", success=False)

        total = len(lines)
        truncated = total > max_lines
        content = "".join(lines[:max_lines])

        if truncated:
            content += f"\n\n[Truncated: showing {max_lines} of {total} lines]"

        return ToolResult(
            output=content,
            success=True,
            ui_payload={"truncated": truncated, "total_lines": total}
            if truncated
            else None,
        )
