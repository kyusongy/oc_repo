import json
import os
import platform
import shutil

from backend.tools.base import Tool, ToolResult

TOOL_CHECKS = [
    "git",
    "python3",
    "python",
    "node",
    "npm",
    "docker",
    "java",
    "go",
    "cargo",
    "ruby",
    "pip",
    "pip3",
    "brew",
    "conda",
    "uv",
]


class CheckSystemTool(Tool):
    name = "check_system"
    description = (
        "Detect the user's operating system, CPU architecture, RAM, disk space, "
        "and which development tools are installed (git, python, node, docker, etc.)."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        installed = {}
        missing = []
        for tool_name in TOOL_CHECKS:
            path = shutil.which(tool_name)
            if path:
                installed[tool_name] = path
            else:
                missing.append(tool_name)

        try:
            import subprocess

            ram_bytes = int(
                subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()
            )
            ram_gb = round(ram_bytes / (1024**3), 1)
        except Exception:
            ram_gb = "unknown"

        statvfs = os.statvfs(os.path.expanduser("~"))
        disk_free_gb = round((statvfs.f_frsize * statvfs.f_bavail) / (1024**3), 1)

        info = {
            "os": platform.system().lower(),
            "arch": platform.machine(),
            "ram_gb": ram_gb,
            "disk_free_gb": disk_free_gb,
            "installed": installed,
            "missing": missing,
        }
        return ToolResult(output=json.dumps(info, indent=2), success=True)
