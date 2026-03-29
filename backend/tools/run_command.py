import asyncio
import os

from backend.tools.base import Tool, ToolResult

DEFAULT_TIMEOUT = 300  # 5 minutes


class RunCommandTool(Tool):
    name = "run_command"
    description = (
        "Execute a shell command on the user's machine. You MUST provide a plain-English "
        "description of what the command does. The user will see this description and must "
        "approve the command before it runs."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "description": {
                "type": "string",
                "description": "Plain-English explanation of what this command does (shown to user)",
            },
            "cwd": {
                "type": "string",
                "description": "Working directory for the command (defaults to the cloned repo path)",
            },
        },
        "required": ["command", "description"],
    }
    requires_approval = True

    def __init__(self):
        self.on_output: callable | None = None

    async def execute(self, params: dict) -> ToolResult:
        command = params["command"]
        cwd = params.get("cwd", os.path.expanduser("~/oc_repo_workspace"))
        timeout = params.get("timeout", DEFAULT_TIMEOUT)

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return ToolResult(
                    output=f"Command timed out after {timeout}s: {command}",
                    success=False,
                    ui_payload={"exit_code": -1, "timed_out": True},
                )

            stdout = stdout_bytes.decode(errors="replace").strip()
            stderr = stderr_bytes.decode(errors="replace").strip()
            exit_code = proc.returncode

            output_parts = []
            if stdout:
                output_parts.append(f"stdout:\n{stdout}")
            if stderr:
                output_parts.append(f"stderr:\n{stderr}")
            if not output_parts:
                output_parts.append("(no output)")

            output = "\n\n".join(output_parts)

            return ToolResult(
                output=output,
                success=exit_code == 0,
                ui_payload={"exit_code": exit_code, "timed_out": False},
            )

        except Exception as e:
            return ToolResult(
                output=f"Error executing command: {e}",
                success=False,
                ui_payload={"exit_code": -1, "timed_out": False},
            )
