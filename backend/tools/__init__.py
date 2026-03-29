from backend.tools.check_system import CheckSystemTool
from backend.tools.clone_repo import CloneRepoTool
from backend.tools.list_files import ListFilesTool
from backend.tools.read_file import ReadFileTool
from backend.tools.run_command import RunCommandTool
from backend.tools.ask_user import AskUserTool
from backend.tools.report_status import ReportStatusTool
from backend.tools.base import ToolRegistry


def create_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            CheckSystemTool(),
            CloneRepoTool(),
            ListFilesTool(),
            ReadFileTool(),
            RunCommandTool(),
            AskUserTool(),
            ReportStatusTool(),
        ]
    )
