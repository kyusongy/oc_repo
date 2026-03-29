import fnmatch
import json
import os

from backend.tools.base import Tool, ToolResult


class ListFilesTool(Tool):
    name = "list_files"
    description = (
        "List files in a directory. Optionally filter by glob pattern (e.g., '*.py'). "
        "Returns a JSON array of file paths. Use max_depth to limit recursion."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list",
            },
            "pattern": {
                "type": "string",
                "description": "Glob pattern to filter files (e.g., '*.py', '*.json')",
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum directory depth to recurse (default 3)",
            },
        },
        "required": ["path"],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        path = params["path"]
        pattern = params.get("pattern")
        max_depth = params.get("max_depth", 3)

        if not os.path.isdir(path):
            return ToolResult(output=f"Directory not found: {path}", success=False)

        files = []
        base_depth = path.rstrip("/").count("/")
        for root, dirs, filenames in os.walk(path):
            depth = root.count("/") - base_depth
            if depth >= max_depth:
                dirs.clear()
                continue
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".") and d != "node_modules" and d != "__pycache__"
            ]
            for name in filenames:
                if name.startswith("."):
                    continue
                if pattern and not fnmatch.fnmatch(name, pattern):
                    continue
                files.append(os.path.join(root, name))

        return ToolResult(output=json.dumps(files, indent=2), success=True)
