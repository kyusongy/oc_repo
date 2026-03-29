# One-Click Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an LLM-powered agent that lets non-technical users paste a GitHub URL and get the project installed and running via a conversational web UI.

**Architecture:** Single-agent with tool-use. FastAPI backend runs the agent loop (LLM ↔ tool execution cycle), React frontend provides a chat UI connected via WebSocket. LLM is called via OpenAI-compatible API (configurable base URL, key, model).

**Tech Stack:** Python 3.12+ (uv), FastAPI, WebSocket, OpenAI SDK, React, TypeScript, Vite, Tailwind CSS

---

## File Map

```
oc_repo/
├── pyproject.toml                  # uv project: backend deps (fastapi, openai, uvicorn)
├── .env.example                    # LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, WebSocket endpoint, CORS
│   ├── session.py                  # Session: wraps WebSocket, manages pending requests
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── engine.py               # agent_loop(): LLM ↔ tools cycle
│   │   ├── prompt.py               # SYSTEM_PROMPT constant, build_tools_schema()
│   │   └── llm.py                  # get_client(), chat() wrapper
│   └── tools/
│       ├── __init__.py             # TOOL_REGISTRY: list of all tool instances
│       ├── base.py                 # Tool ABC, ToolResult dataclass
│       ├── check_system.py         # CheckSystemTool
│       ├── clone_repo.py           # CloneRepoTool
│       ├── list_files.py           # ListFilesTool
│       ├── read_file.py            # ReadFileTool
│       ├── run_command.py          # RunCommandTool (requires approval + streaming)
│       ├── ask_user.py             # AskUserTool (requires session for WebSocket I/O)
│       └── report_status.py        # ReportStatusTool (requires session)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures (tmp dirs, mock session)
│   ├── test_base.py                # Tool ABC, ToolResult, ToolRegistry
│   ├── test_check_system.py
│   ├── test_clone_repo.py
│   ├── test_list_files.py
│   ├── test_read_file.py
│   ├── test_run_command.py
│   ├── test_engine.py              # Agent loop with mocked LLM
│   └── test_main.py                # WebSocket endpoint integration
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                 # Top-level: URL input state → ChatWindow
│   │   ├── types.ts                # WebSocket message types (shared contract)
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts     # Connect, send, receive, reconnect
│   │   └── components/
│   │       ├── UrlInput.tsx         # GitHub URL input + Go button
│   │       ├── StatusBar.tsx        # Phase indicator (Scanning → Installing → Done)
│   │       ├── ChatWindow.tsx       # Scrollable message list, dispatches to renderers
│   │       ├── MessageBubble.tsx    # Agent/user text messages (markdown)
│   │       ├── ApprovalCard.tsx     # Command + description + Approve/Deny
│   │       ├── UserInputWidget.tsx  # Text/password/choice input inline
│   │       └── TerminalOutput.tsx   # Collapsible raw command output
│   └── public/
└── docs/
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `backend/__init__.py`
- Create: `backend/agent/__init__.py`
- Create: `backend/tools/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Users/kyle/projects/oc_repo
uv init --no-readme
```

- [ ] **Step 2: Update pyproject.toml with dependencies**

Replace contents of `pyproject.toml`:

```toml
[project]
name = "oc-repo"
version = "0.1.0"
description = "One-Click Repo: LLM-powered GitHub repo installer for non-technical users"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "openai>=1.60.0",
    "python-dotenv>=1.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
]
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

- [ ] **Step 4: Create .env.example**

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
```

- [ ] **Step 5: Create .gitignore**

```
__pycache__/
*.pyc
.env
.venv/
node_modules/
dist/
.uv/
uv.lock
```

- [ ] **Step 6: Create package __init__.py files**

Create empty files:
- `backend/__init__.py`
- `backend/agent/__init__.py`
- `backend/tools/__init__.py`
- `tests/__init__.py`

- [ ] **Step 7: Scaffold frontend with Vite**

```bash
cd /Users/kyle/projects/oc_repo
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 8: Configure Tailwind**

Replace `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
```

Replace `frontend/src/index.css`:

```css
@import "tailwindcss";
```

- [ ] **Step 9: Verify setup**

```bash
cd /Users/kyle/projects/oc_repo
uv run python -c "import fastapi; import openai; print('Backend OK')"
cd frontend && npm run build && echo "Frontend OK"
```

Expected: Both print OK.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "Scaffold project with uv and Vite"
```

---

### Task 2: Tool Framework (base.py)

**Files:**
- Create: `backend/tools/base.py`
- Create: `tests/test_base.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write failing tests for Tool ABC and ToolResult**

Create `tests/conftest.py`:

```python
import asyncio
import pytest


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a fake repo directory with some files."""
    (tmp_path / "README.md").write_text("# Test Project\nInstall with npm install")
    (tmp_path / "package.json").write_text('{"name": "test", "version": "1.0.0"}')
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.js").write_text("console.log('hello')")
    return tmp_path
```

Create `tests/test_base.py`:

```python
import pytest
from backend.tools.base import Tool, ToolResult, ToolRegistry


def test_tool_result_success():
    result = ToolResult(output="done", success=True)
    assert result.output == "done"
    assert result.success is True
    assert result.ui_payload is None


def test_tool_result_with_payload():
    result = ToolResult(output="data", success=True, ui_payload={"key": "val"})
    assert result.ui_payload == {"key": "val"}


class DummyTool(Tool):
    name = "dummy"
    description = "A test tool"
    parameters = {"type": "object", "properties": {"x": {"type": "string"}}}
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(output=f"got {params['x']}", success=True)


@pytest.mark.asyncio
async def test_tool_execute():
    tool = DummyTool()
    result = await tool.execute({"x": "hello"})
    assert result.output == "got hello"
    assert result.success is True


def test_tool_schema():
    tool = DummyTool()
    schema = tool.to_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "dummy"
    assert schema["function"]["description"] == "A test tool"
    assert schema["function"]["parameters"] == tool.parameters


def test_registry_get():
    tool = DummyTool()
    registry = ToolRegistry([tool])
    assert registry.get("dummy") is tool


def test_registry_get_missing():
    registry = ToolRegistry([])
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_registry_schemas():
    tool = DummyTool()
    registry = ToolRegistry([tool])
    schemas = registry.schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "dummy"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/kyle/projects/oc_repo
uv run pytest tests/test_base.py -v
```

Expected: ModuleNotFoundError — `backend.tools.base` doesn't exist yet.

- [ ] **Step 3: Implement base.py**

Create `backend/tools/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    output: str
    success: bool
    ui_payload: dict | None = None


class Tool(ABC):
    name: str
    description: str
    parameters: dict
    requires_approval: bool = False

    @abstractmethod
    async def execute(self, params: dict) -> ToolResult: ...

    def to_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self._tools = {t.name: t for t in tools}

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def schemas(self) -> list[dict]:
        return [t.to_schema() for t in self._tools.values()]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_base.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tools/base.py tests/test_base.py tests/conftest.py
git commit -m "Add Tool ABC, ToolResult, and ToolRegistry"
```

---

### Task 3: check_system Tool

**Files:**
- Create: `backend/tools/check_system.py`
- Create: `tests/test_check_system.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_check_system.py`:

```python
import pytest
from backend.tools.check_system import CheckSystemTool


@pytest.mark.asyncio
async def test_check_system_returns_os():
    tool = CheckSystemTool()
    result = await tool.execute({})
    assert result.success is True
    assert "os" in result.output
    assert "darwin" in result.output.lower()  # macOS


@pytest.mark.asyncio
async def test_check_system_detects_git():
    tool = CheckSystemTool()
    result = await tool.execute({})
    # git should be installed on the dev machine
    assert "git" in result.output.lower()


@pytest.mark.asyncio
async def test_check_system_schema():
    tool = CheckSystemTool()
    schema = tool.to_schema()
    assert schema["function"]["name"] == "check_system"
    # No required params
    assert schema["function"]["parameters"]["properties"] == {}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_check_system.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement check_system.py**

Create `backend/tools/check_system.py`:

```python
import json
import os
import platform
import shutil

from backend.tools.base import Tool, ToolResult

# Tools to detect and their common binary names
TOOL_CHECKS = [
    "git", "python3", "python", "node", "npm", "docker",
    "java", "go", "cargo", "ruby", "pip", "pip3", "brew",
    "conda", "uv",
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
            ram_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_check_system.py -v
```

Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tools/check_system.py tests/test_check_system.py
git commit -m "Add check_system tool"
```

---

### Task 4: clone_repo Tool

**Files:**
- Create: `backend/tools/clone_repo.py`
- Create: `tests/test_clone_repo.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_clone_repo.py`:

```python
import os
import pytest
from backend.tools.clone_repo import CloneRepoTool

WORKSPACE = os.path.expanduser("~/oc_repo_workspace")


@pytest.mark.asyncio
async def test_clone_repo_valid(tmp_path, monkeypatch):
    # Use tmp_path as workspace so we don't pollute the real one
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = CloneRepoTool()
    result = await tool.execute({"url": "https://github.com/octocat/Hello-World.git"})
    assert result.success is True
    assert "Hello-World" in result.output
    cloned_path = tmp_path / "Hello-World"
    assert cloned_path.exists()
    assert (cloned_path / ".git").exists()


@pytest.mark.asyncio
async def test_clone_repo_invalid_url(tmp_path, monkeypatch):
    monkeypatch.setenv("OC_WORKSPACE", str(tmp_path))
    tool = CloneRepoTool()
    result = await tool.execute({"url": "https://github.com/not-a-real-user/not-a-real-repo-12345.git"})
    assert result.success is False
    assert "error" in result.output.lower() or "fatal" in result.output.lower()


@pytest.mark.asyncio
async def test_clone_repo_schema():
    tool = CloneRepoTool()
    schema = tool.to_schema()
    assert schema["function"]["name"] == "clone_repo"
    assert "url" in schema["function"]["parameters"]["properties"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_clone_repo.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement clone_repo.py**

Create `backend/tools/clone_repo.py`:

```python
import asyncio
import os
import re

from backend.tools.base import Tool, ToolResult


def _repo_name(url: str) -> str:
    """Extract repo name from GitHub URL."""
    # Handle both https://github.com/user/repo and https://github.com/user/repo.git
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name.removesuffix(".git")


def _workspace() -> str:
    return os.environ.get("OC_WORKSPACE", os.path.expanduser("~/oc_repo_workspace"))


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
            "git", "clone", "--depth", "1", url, target,
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_clone_repo.py -v
```

Expected: All 3 tests PASS. (The valid clone test requires network access.)

- [ ] **Step 5: Commit**

```bash
git add backend/tools/clone_repo.py tests/test_clone_repo.py
git commit -m "Add clone_repo tool"
```

---

### Task 5: list_files and read_file Tools

**Files:**
- Create: `backend/tools/list_files.py`
- Create: `backend/tools/read_file.py`
- Create: `tests/test_list_files.py`
- Create: `tests/test_read_file.py`

- [ ] **Step 1: Write failing tests for list_files**

Create `tests/test_list_files.py`:

```python
import json
import pytest
from backend.tools.list_files import ListFilesTool


@pytest.mark.asyncio
async def test_list_files_basic(tmp_repo):
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo)})
    assert result.success is True
    files = json.loads(result.output)
    names = [f.rsplit("/", 1)[-1] for f in files]
    assert "README.md" in names
    assert "package.json" in names


@pytest.mark.asyncio
async def test_list_files_with_pattern(tmp_repo):
    tool = ListFilesTool()
    result = await tool.execute({"path": str(tmp_repo), "pattern": "*.md"})
    files = json.loads(result.output)
    assert len(files) == 1
    assert files[0].endswith("README.md")


@pytest.mark.asyncio
async def test_list_files_nonexistent():
    tool = ListFilesTool()
    result = await tool.execute({"path": "/nonexistent/path"})
    assert result.success is False
```

- [ ] **Step 2: Write failing tests for read_file**

Create `tests/test_read_file.py`:

```python
import pytest
from backend.tools.read_file import ReadFileTool


@pytest.mark.asyncio
async def test_read_file_basic(tmp_repo):
    tool = ReadFileTool()
    result = await tool.execute({"path": str(tmp_repo / "README.md")})
    assert result.success is True
    assert "# Test Project" in result.output


@pytest.mark.asyncio
async def test_read_file_max_lines(tmp_path):
    # Create a file with 100 lines
    f = tmp_path / "big.txt"
    f.write_text("\n".join(f"line {i}" for i in range(100)))
    tool = ReadFileTool()
    result = await tool.execute({"path": str(f), "max_lines": 5})
    assert result.success is True
    assert "line 4" in result.output
    assert "line 5" not in result.output
    assert "truncated" in result.output.lower() or result.ui_payload


@pytest.mark.asyncio
async def test_read_file_nonexistent():
    tool = ReadFileTool()
    result = await tool.execute({"path": "/nonexistent/file.txt"})
    assert result.success is False
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run pytest tests/test_list_files.py tests/test_read_file.py -v
```

Expected: ModuleNotFoundError for both.

- [ ] **Step 4: Implement list_files.py**

Create `backend/tools/list_files.py`:

```python
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
            # Skip hidden dirs and common noise
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules" and d != "__pycache__"]
            for name in filenames:
                if name.startswith("."):
                    continue
                if pattern and not fnmatch.fnmatch(name, pattern):
                    continue
                files.append(os.path.join(root, name))

        return ToolResult(output=json.dumps(files, indent=2), success=True)
```

- [ ] **Step 5: Implement read_file.py**

Create `backend/tools/read_file.py`:

```python
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
            ui_payload={"truncated": truncated, "total_lines": total} if truncated else None,
        )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_list_files.py tests/test_read_file.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/tools/list_files.py backend/tools/read_file.py tests/test_list_files.py tests/test_read_file.py
git commit -m "Add list_files and read_file tools"
```

---

### Task 6: run_command Tool

**Files:**
- Create: `backend/tools/run_command.py`
- Create: `tests/test_run_command.py`

This is the most critical tool. It executes shell commands, streams output, and handles timeouts.

- [ ] **Step 1: Write failing tests**

Create `tests/test_run_command.py`:

```python
import pytest
from backend.tools.run_command import RunCommandTool


@pytest.mark.asyncio
async def test_run_command_success(tmp_path):
    tool = RunCommandTool()
    result = await tool.execute({
        "command": "echo hello world",
        "description": "Print hello world",
        "cwd": str(tmp_path),
    })
    assert result.success is True
    assert "hello world" in result.output


@pytest.mark.asyncio
async def test_run_command_failure(tmp_path):
    tool = RunCommandTool()
    result = await tool.execute({
        "command": "ls /nonexistent_dir_12345",
        "description": "List a nonexistent directory",
        "cwd": str(tmp_path),
    })
    assert result.success is False
    assert result.ui_payload["exit_code"] != 0


@pytest.mark.asyncio
async def test_run_command_timeout(tmp_path):
    tool = RunCommandTool()
    # Override timeout to 1 second for testing
    result = await tool.execute({
        "command": "sleep 10",
        "description": "Sleep for 10 seconds",
        "cwd": str(tmp_path),
        "timeout": 1,
    })
    assert result.success is False
    assert result.ui_payload["timed_out"] is True


@pytest.mark.asyncio
async def test_run_command_cwd(tmp_path):
    (tmp_path / "testfile.txt").write_text("hi")
    tool = RunCommandTool()
    result = await tool.execute({
        "command": "ls testfile.txt",
        "description": "List testfile in cwd",
        "cwd": str(tmp_path),
    })
    assert result.success is True
    assert "testfile.txt" in result.output


@pytest.mark.asyncio
async def test_run_command_schema():
    tool = RunCommandTool()
    schema = tool.to_schema()
    props = schema["function"]["parameters"]["properties"]
    assert "command" in props
    assert "description" in props
    assert "cwd" in props
    assert tool.requires_approval is True
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_run_command.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement run_command.py**

Create `backend/tools/run_command.py`:

```python
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
        self.on_output: callable | None = None  # Set by engine for streaming

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_run_command.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tools/run_command.py tests/test_run_command.py
git commit -m "Add run_command tool with timeout support"
```

---

### Task 7: Session + ask_user + report_status Tools

**Files:**
- Create: `backend/session.py`
- Create: `backend/tools/ask_user.py`
- Create: `backend/tools/report_status.py`

These tools need a Session object to communicate with the frontend via WebSocket.

- [ ] **Step 1: Implement session.py**

Create `backend/session.py`:

```python
import asyncio
import json
import uuid


class Session:
    """Manages WebSocket communication between tools and the frontend."""

    def __init__(self, send_fn):
        """
        Args:
            send_fn: async callable that sends a dict to the frontend WebSocket.
        """
        self.send = send_fn
        self._pending: dict[str, asyncio.Future] = {}

    async def request_approval(self, command: str, description: str) -> bool:
        request_id = str(uuid.uuid4())
        await self.send({
            "type": "approval_request",
            "request_id": request_id,
            "command": command,
            "description": description,
        })
        future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        return await future

    async def request_input(
        self, question: str, options: list[dict] | None = None, input_type: str = "text"
    ) -> str:
        request_id = str(uuid.uuid4())
        msg = {
            "type": "user_input_request",
            "request_id": request_id,
            "question": question,
            "input_type": input_type,
        }
        if options:
            msg["options"] = options
        await self.send(msg)
        future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        return await future

    async def send_output(self, stream: str, text: str):
        await self.send({
            "type": "command_output",
            "stream": stream,
            "text": text,
        })

    async def send_status(self, phase: str, message: str, progress: float | None = None):
        msg = {"type": "status_update", "phase": phase, "message": message}
        if progress is not None:
            msg["progress"] = progress
        await self.send(msg)

    def resolve(self, request_id: str, value):
        """Called when frontend sends a response to a pending request."""
        future = self._pending.pop(request_id, None)
        if future and not future.done():
            future.set_result(value)
```

- [ ] **Step 2: Implement ask_user.py**

Create `backend/tools/ask_user.py`:

```python
from backend.tools.base import Tool, ToolResult


class AskUserTool(Tool):
    name = "ask_user"
    description = (
        "Ask the user a question and wait for their response. Use this when you need "
        "information like an API key, a configuration choice, or confirmation. "
        "Use input_type='password' for sensitive values like API keys."
    )
    parameters = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question to ask the user",
            },
            "options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["label", "description"],
                },
                "description": "Multiple choice options (omit for free-text input)",
            },
            "input_type": {
                "type": "string",
                "enum": ["text", "password", "choice"],
                "description": "Type of input widget to show (default: text)",
            },
        },
        "required": ["question"],
    }
    requires_approval = False

    def __init__(self):
        self.session = None  # Set by engine before execution

    async def execute(self, params: dict) -> ToolResult:
        if not self.session:
            return ToolResult(output="Error: no session available", success=False)

        question = params["question"]
        options = params.get("options")
        input_type = params.get("input_type", "text")

        answer = await self.session.request_input(question, options, input_type)
        return ToolResult(output=answer, success=True)
```

- [ ] **Step 3: Implement report_status.py**

Create `backend/tools/report_status.py`:

```python
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
        self.session = None  # Set by engine before execution

    async def execute(self, params: dict) -> ToolResult:
        if not self.session:
            return ToolResult(output="Error: no session available", success=False)

        await self.session.send_status(
            phase=params["phase"],
            message=params["message"],
            progress=params.get("progress"),
        )
        return ToolResult(output="Status updated", success=True)
```

- [ ] **Step 4: Create tool registry in tools/__init__.py**

Update `backend/tools/__init__.py`:

```python
from backend.tools.check_system import CheckSystemTool
from backend.tools.clone_repo import CloneRepoTool
from backend.tools.list_files import ListFilesTool
from backend.tools.read_file import ReadFileTool
from backend.tools.run_command import RunCommandTool
from backend.tools.ask_user import AskUserTool
from backend.tools.report_status import ReportStatusTool
from backend.tools.base import ToolRegistry


def create_registry() -> ToolRegistry:
    return ToolRegistry([
        CheckSystemTool(),
        CloneRepoTool(),
        ListFilesTool(),
        ReadFileTool(),
        RunCommandTool(),
        AskUserTool(),
        ReportStatusTool(),
    ])
```

- [ ] **Step 5: Run all tool tests**

```bash
uv run pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/session.py backend/tools/ask_user.py backend/tools/report_status.py backend/tools/__init__.py
git commit -m "Add Session, ask_user, report_status tools, and registry"
```

---

### Task 8: LLM Client

**Files:**
- Create: `backend/agent/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_llm.py`:

```python
import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.agent.llm import get_client, chat


def test_get_client_reads_env(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://test.api.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    client = get_client()
    assert client.base_url.host == "test.api.com"


def test_get_client_missing_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        get_client()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement llm.py**

Create `backend/agent/llm.py`:

```python
import os
from openai import AsyncOpenAI


def get_client() -> AsyncOpenAI:
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is required")

    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")

    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def get_model() -> str:
    return os.environ.get("LLM_MODEL", "gpt-4o")


async def chat(client: AsyncOpenAI, model: str, messages: list[dict], tools: list[dict]):
    """Call the LLM with messages and tools. Returns the response."""
    kwargs = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return await client.chat.completions.create(**kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_llm.py -v
```

Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agent/llm.py tests/test_llm.py
git commit -m "Add LLM client with OpenAI-compatible config"
```

---

### Task 9: System Prompt

**Files:**
- Create: `backend/agent/prompt.py`

- [ ] **Step 1: Create prompt.py**

Create `backend/agent/prompt.py`:

```python
SYSTEM_PROMPT = """\
You are One-Click Repo, a friendly installation assistant.
Your job is to help non-technical users install and run GitHub projects on their computer.

## How You Work

1. First, check the user's system to see what tools they have installed.
2. Clone the repository they want to install.
3. Read the README and configuration files to understand what the project needs.
4. Assess whether this project can be installed on their machine. If not, explain why in simple terms.
5. If it can be installed, guide them through the setup step by step.
6. After everything is installed, launch the project and confirm it's running.

## Rules

- Explain everything in plain, non-technical language. The user may never have used a terminal before.
- Always describe what a command does BEFORE running it. Use the `description` field in run_command to explain in plain English.
- If something fails, read the error output carefully, diagnose the issue, and try to fix it. You can retry up to 3 times per step.
- If you can't fix an error after retrying, explain the problem honestly in simple terms and suggest what the user might do.
- Never run destructive commands (rm -rf, format, sudo rm, etc.).
- Ask the user before doing anything that requires credentials (API keys, tokens) or costs money.
- Use report_status to keep the UI status bar updated as you move through phases.

## Phases

Use report_status to signal phase transitions:
- "scanning" — while checking the system and analyzing the repo
- "installing" — while installing dependencies and configuring
- "launching" — while starting the project
- "done" — when the project is running successfully
- "error" — if something goes wrong that you can't fix
"""
```

- [ ] **Step 2: Commit**

```bash
git add backend/agent/prompt.py
git commit -m "Add system prompt"
```

---

### Task 10: Agent Engine

**Files:**
- Create: `backend/agent/engine.py`
- Create: `tests/test_engine.py`

This is the core loop: LLM ↔ tool execution cycle.

- [ ] **Step 1: Write failing test**

Create `tests/test_engine.py`:

```python
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.agent.engine import AgentEngine
from backend.tools.base import Tool, ToolResult, ToolRegistry
from backend.session import Session


class EchoTool(Tool):
    name = "echo"
    description = "Echo back the input"
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }
    requires_approval = False

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(output=f"echoed: {params['text']}", success=True)


def _make_text_response(text: str):
    """Create a mock LLM response with text content (no tool calls)."""
    choice = MagicMock()
    choice.message.content = text
    choice.message.tool_calls = None
    choice.finish_reason = "stop"
    response = MagicMock()
    response.choices = [choice]
    return response


def _make_tool_response(tool_name: str, arguments: dict):
    """Create a mock LLM response with a tool call."""
    tool_call = MagicMock()
    tool_call.id = "call_123"
    tool_call.function.name = tool_name
    tool_call.function.arguments = json.dumps(arguments)
    choice = MagicMock()
    choice.message.content = None
    choice.message.tool_calls = [tool_call]
    choice.finish_reason = "tool_calls"
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.mark.asyncio
async def test_engine_text_response():
    """When LLM responds with text, engine yields it and stops."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = _make_text_response("Hello!")

    registry = ToolRegistry([EchoTool()])
    engine = AgentEngine(mock_client, "test-model", registry)

    messages = []
    async for msg in engine.run("Hi", messages):
        assert msg == "Hello!"


@pytest.mark.asyncio
async def test_engine_tool_call_then_text():
    """LLM calls a tool, gets result, then responds with text."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        _make_tool_response("echo", {"text": "test"}),
        _make_text_response("I echoed: test"),
    ]

    registry = ToolRegistry([EchoTool()])
    engine = AgentEngine(mock_client, "test-model", registry)

    messages = []
    results = []
    async for msg in engine.run("Echo something", messages):
        results.append(msg)

    assert len(results) == 1
    assert "I echoed: test" in results[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_engine.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement engine.py**

Create `backend/agent/engine.py`:

```python
import json

from openai import AsyncOpenAI

from backend.agent.prompt import SYSTEM_PROMPT
from backend.session import Session
from backend.tools.base import ToolRegistry


class AgentEngine:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        registry: ToolRegistry,
        session: Session | None = None,
    ):
        self.client = client
        self.model = model
        self.registry = registry
        self.session = session

    async def run(self, user_message: str, history: list[dict]):
        """Run the agent loop. Yields text messages from the agent."""
        if not history:
            history.append({"role": "system", "content": SYSTEM_PROMPT})

        history.append({"role": "user", "content": user_message})

        tools = self.registry.schemas()

        while True:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=history,
                tools=tools if tools else None,
            )

            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                # Add assistant message with tool calls to history
                history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                })

                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    arguments = json.loads(tc.function.arguments)

                    tool = self.registry.get(tool_name)

                    # Inject session into tools that need it
                    if hasattr(tool, "session") and self.session:
                        tool.session = self.session

                    # Handle approval for tools that require it
                    if tool.requires_approval and self.session:
                        description = arguments.get("description", tool_name)
                        command = arguments.get("command", str(arguments))
                        approved = await self.session.request_approval(command, description)
                        if not approved:
                            history.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": "User denied this action.",
                            })
                            continue

                    result = await tool.execute(arguments)

                    # Stream command output if session is available
                    if tool_name == "run_command" and self.session:
                        await self.session.send_output("stdout", result.output)

                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result.output,
                    })
            else:
                # LLM responded with text — yield to frontend
                text = message.content or ""
                history.append({"role": "assistant", "content": text})
                yield text
                return
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_engine.py -v
```

Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/agent/engine.py tests/test_engine.py
git commit -m "Add agent engine with tool-use loop"
```

---

### Task 11: FastAPI WebSocket Server

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_main.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_main.py -v
```

Expected: ModuleNotFoundError.

- [ ] **Step 3: Implement main.py**

Create `backend/main.py`:

```python
import asyncio
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.engine import AgentEngine
from backend.agent.llm import get_client, get_model
from backend.session import Session
from backend.tools import create_registry

load_dotenv()

app = FastAPI(title="One-Click Repo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    async def send_fn(msg: dict):
        await ws.send_json(msg)

    session = Session(send_fn)
    registry = create_registry()

    try:
        client = get_client()
        model = get_model()
    except ValueError as e:
        await ws.send_json({"type": "agent_message", "text": f"Configuration error: {e}"})
        await ws.close()
        return

    engine = AgentEngine(client, model, registry, session)
    history: list[dict] = []
    agent_task: asyncio.Task | None = None

    async def run_agent(user_msg: str):
        """Run the agent loop as a background task so WebSocket stays responsive."""
        try:
            async for text in engine.run(user_msg, history):
                await ws.send_json({"type": "agent_message", "text": text})
        except Exception as e:
            await ws.send_json({"type": "agent_message", "text": f"Error: {e}"})

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "start":
                url = data.get("url", "")
                user_msg = f"Please install this GitHub repository: {url}"
                # Run agent in background so we can still receive approval/input messages
                agent_task = asyncio.create_task(run_agent(user_msg))

            elif msg_type == "message":
                user_msg = data.get("text", "")
                agent_task = asyncio.create_task(run_agent(user_msg))

            elif msg_type == "approval":
                request_id = data.get("request_id")
                approved = data.get("approved", False)
                session.resolve(request_id, approved)

            elif msg_type == "user_input":
                request_id = data.get("request_id")
                value = data.get("value", "")
                session.resolve(request_id, value)

    except WebSocketDisconnect:
        if agent_task:
            agent_task.cancel()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_main.py -v
```

Expected: PASS.

- [ ] **Step 5: Verify server starts**

```bash
cd /Users/kyle/projects/oc_repo
timeout 3 uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 || true
```

Expected: Server starts (then times out after 3s — that's fine, just verifying it boots).

- [ ] **Step 6: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "Add FastAPI WebSocket server"
```

---

### Task 12: Frontend Types and WebSocket Hook

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create shared types**

Create `frontend/src/types.ts`:

```typescript
// Messages FROM backend
export type ServerMessage =
  | { type: "agent_message"; text: string }
  | {
      type: "approval_request";
      request_id: string;
      command: string;
      description: string;
    }
  | {
      type: "user_input_request";
      request_id: string;
      question: string;
      options?: { label: string; description: string }[];
      input_type: "text" | "password" | "choice";
    }
  | { type: "command_output"; stream: "stdout" | "stderr"; text: string }
  | {
      type: "status_update";
      phase: string;
      message: string;
      progress?: number;
    }
  | { type: "done"; success: boolean; message: string };

// Messages TO backend
export type ClientMessage =
  | { type: "start"; url: string }
  | { type: "message"; text: string }
  | { type: "approval"; request_id: string; approved: boolean }
  | { type: "user_input"; request_id: string; value: string };

// UI state for chat messages
export type ChatMessage =
  | { kind: "agent"; text: string }
  | { kind: "user"; text: string }
  | {
      kind: "approval";
      request_id: string;
      command: string;
      description: string;
      resolved?: boolean;
    }
  | {
      kind: "input";
      request_id: string;
      question: string;
      options?: { label: string; description: string }[];
      input_type: "text" | "password" | "choice";
      resolved?: boolean;
    }
  | { kind: "output"; stream: "stdout" | "stderr"; text: string };

export type Phase =
  | "idle"
  | "scanning"
  | "installing"
  | "launching"
  | "done"
  | "error";
```

- [ ] **Step 2: Create WebSocket hook**

Create `frontend/src/hooks/useWebSocket.ts`:

```typescript
import { useCallback, useEffect, useRef, useState } from "react";
import type { ClientMessage, ServerMessage } from "../types";

type MessageHandler = (msg: ServerMessage) => void;

export function useWebSocket(onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg: ServerMessage = JSON.parse(event.data);
        onMessage(msg);
      } catch {
        console.error("Failed to parse WebSocket message:", event.data);
      }
    };

    wsRef.current = ws;
    return () => ws.close();
  }, [onMessage]);

  const send = useCallback((msg: ClientMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { send, connected };
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/kyle/projects/oc_repo
git add frontend/src/types.ts frontend/src/hooks/useWebSocket.ts
git commit -m "Add frontend types and WebSocket hook"
```

---

### Task 13: UrlInput and StatusBar Components

**Files:**
- Create: `frontend/src/components/UrlInput.tsx`
- Create: `frontend/src/components/StatusBar.tsx`

- [ ] **Step 1: Create UrlInput**

Create `frontend/src/components/UrlInput.tsx`:

```tsx
import { useState } from "react";

interface Props {
  onSubmit: (url: string) => void;
  disabled?: boolean;
}

export function UrlInput({ onSubmit, disabled }: Props) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSubmit(url.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4">
      <input
        type="text"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="Paste a GitHub repo URL (e.g., https://github.com/user/repo)"
        disabled={disabled}
        className="flex-1 px-4 py-3 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={disabled || !url.trim()}
        className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Go
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Create StatusBar**

Create `frontend/src/components/StatusBar.tsx`:

```tsx
import type { Phase } from "../types";

const PHASE_LABELS: Record<Phase, string> = {
  idle: "Ready",
  scanning: "Scanning repo...",
  installing: "Installing...",
  launching: "Launching...",
  done: "Done!",
  error: "Error",
};

const PHASE_COLORS: Record<Phase, string> = {
  idle: "bg-gray-200 text-gray-600",
  scanning: "bg-yellow-100 text-yellow-800",
  installing: "bg-blue-100 text-blue-800",
  launching: "bg-purple-100 text-purple-800",
  done: "bg-green-100 text-green-800",
  error: "bg-red-100 text-red-800",
};

interface Props {
  phase: Phase;
  message?: string;
  progress?: number;
}

export function StatusBar({ phase, message, progress }: Props) {
  if (phase === "idle") return null;

  return (
    <div className={`px-4 py-2 text-sm font-medium ${PHASE_COLORS[phase]}`}>
      <div className="flex items-center justify-between">
        <span>{message || PHASE_LABELS[phase]}</span>
        {progress != null && (
          <span className="text-xs">{Math.round(progress)}%</span>
        )}
      </div>
      {progress != null && (
        <div className="mt-1 h-1 bg-black/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-current rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/UrlInput.tsx frontend/src/components/StatusBar.tsx
git commit -m "Add UrlInput and StatusBar components"
```

---

### Task 14: MessageBubble and TerminalOutput Components

**Files:**
- Create: `frontend/src/components/MessageBubble.tsx`
- Create: `frontend/src/components/TerminalOutput.tsx`

- [ ] **Step 1: Install markdown renderer**

```bash
cd /Users/kyle/projects/oc_repo/frontend
npm install react-markdown
```

- [ ] **Step 2: Create MessageBubble**

Create `frontend/src/components/MessageBubble.tsx`:

```tsx
import ReactMarkdown from "react-markdown";

interface Props {
  role: "agent" | "user";
  text: string;
}

export function MessageBubble({ role, text }: Props) {
  const isAgent = role === "agent";

  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"} mb-3`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl ${
          isAgent
            ? "bg-gray-100 text-gray-900 rounded-bl-sm"
            : "bg-blue-600 text-white rounded-br-sm"
        }`}
      >
        {isAgent ? (
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{text}</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create TerminalOutput**

Create `frontend/src/components/TerminalOutput.tsx`:

```tsx
import { useState } from "react";

interface Props {
  stream: "stdout" | "stderr";
  text: string;
}

export function TerminalOutput({ stream, text }: Props) {
  const [expanded, setExpanded] = useState(false);

  const lines = text.split("\n");
  const preview = lines.slice(0, 3).join("\n");
  const hasMore = lines.length > 3;

  return (
    <div className="mb-3 mx-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-1"
      >
        <span className={`transform transition-transform ${expanded ? "rotate-90" : ""}`}>
          ▶
        </span>
        <span>
          {stream === "stderr" ? "Error output" : "Terminal output"} ({lines.length} lines)
        </span>
      </button>
      <pre
        className={`text-xs font-mono p-3 rounded-lg overflow-x-auto ${
          stream === "stderr"
            ? "bg-red-50 text-red-800 border border-red-200"
            : "bg-gray-900 text-green-400"
        }`}
      >
        {expanded ? text : preview}
        {hasMore && !expanded && (
          <span className="text-gray-500">{"\n"}... click to expand</span>
        )}
      </pre>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/MessageBubble.tsx frontend/src/components/TerminalOutput.tsx
git commit -m "Add MessageBubble and TerminalOutput components"
```

---

### Task 15: ApprovalCard and UserInputWidget Components

**Files:**
- Create: `frontend/src/components/ApprovalCard.tsx`
- Create: `frontend/src/components/UserInputWidget.tsx`

- [ ] **Step 1: Create ApprovalCard**

Create `frontend/src/components/ApprovalCard.tsx`:

```tsx
interface Props {
  command: string;
  description: string;
  resolved?: boolean;
  onApprove: () => void;
  onDeny: () => void;
}

export function ApprovalCard({
  command,
  description,
  resolved,
  onApprove,
  onDeny,
}: Props) {
  return (
    <div className="mb-3 mx-2 border border-amber-200 bg-amber-50 rounded-lg p-4">
      <p className="text-sm text-gray-700 mb-2">{description}</p>
      <pre className="text-xs font-mono bg-gray-900 text-green-400 p-3 rounded-md mb-3 overflow-x-auto">
        {command}
      </pre>
      {resolved ? (
        <p className="text-xs text-gray-500 italic">Responded</p>
      ) : (
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors"
          >
            Approve
          </button>
          <button
            onClick={onDeny}
            className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-md hover:bg-red-200 transition-colors"
          >
            Deny
          </button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create UserInputWidget**

Create `frontend/src/components/UserInputWidget.tsx`:

```tsx
import { useState } from "react";

interface Props {
  question: string;
  options?: { label: string; description: string }[];
  inputType: "text" | "password" | "choice";
  resolved?: boolean;
  onSubmit: (value: string) => void;
}

export function UserInputWidget({
  question,
  options,
  inputType,
  resolved,
  onSubmit,
}: Props) {
  const [value, setValue] = useState("");

  if (resolved) {
    return (
      <div className="mb-3 mx-2 border border-gray-200 bg-gray-50 rounded-lg p-4">
        <p className="text-sm text-gray-700">{question}</p>
        <p className="text-xs text-gray-500 italic mt-1">Answered</p>
      </div>
    );
  }

  // Choice input
  if (inputType === "choice" && options) {
    return (
      <div className="mb-3 mx-2 border border-blue-200 bg-blue-50 rounded-lg p-4">
        <p className="text-sm text-gray-700 mb-3">{question}</p>
        <div className="flex flex-col gap-2">
          {options.map((opt) => (
            <button
              key={opt.label}
              onClick={() => onSubmit(opt.label)}
              className="text-left px-3 py-2 bg-white border border-gray-200 rounded-md hover:bg-blue-100 hover:border-blue-300 transition-colors"
            >
              <span className="text-sm font-medium">{opt.label}</span>
              {opt.description && (
                <span className="text-xs text-gray-500 block">
                  {opt.description}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // Text or password input
  return (
    <div className="mb-3 mx-2 border border-blue-200 bg-blue-50 rounded-lg p-4">
      <p className="text-sm text-gray-700 mb-2">{question}</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (value.trim()) onSubmit(value.trim());
        }}
        className="flex gap-2"
      >
        <input
          type={inputType === "password" ? "password" : "text"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={inputType === "password" ? "••••••••" : "Type your answer..."}
          className="flex-1 px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={!value.trim()}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Submit
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ApprovalCard.tsx frontend/src/components/UserInputWidget.tsx
git commit -m "Add ApprovalCard and UserInputWidget components"
```

---

### Task 16: ChatWindow Component

**Files:**
- Create: `frontend/src/components/ChatWindow.tsx`

- [ ] **Step 1: Create ChatWindow**

Create `frontend/src/components/ChatWindow.tsx`:

```tsx
import { useEffect, useRef } from "react";
import type { ChatMessage, ClientMessage } from "../types";
import { MessageBubble } from "./MessageBubble";
import { ApprovalCard } from "./ApprovalCard";
import { UserInputWidget } from "./UserInputWidget";
import { TerminalOutput } from "./TerminalOutput";

interface Props {
  messages: ChatMessage[];
  onSend: (msg: ClientMessage) => void;
}

export function ChatWindow({ messages, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-400 mt-20">
          <p className="text-lg">Paste a GitHub repo URL above to get started</p>
        </div>
      )}

      {messages.map((msg, i) => {
        switch (msg.kind) {
          case "agent":
            return <MessageBubble key={i} role="agent" text={msg.text} />;
          case "user":
            return <MessageBubble key={i} role="user" text={msg.text} />;
          case "approval":
            return (
              <ApprovalCard
                key={i}
                command={msg.command}
                description={msg.description}
                resolved={msg.resolved}
                onApprove={() =>
                  onSend({
                    type: "approval",
                    request_id: msg.request_id,
                    approved: true,
                  })
                }
                onDeny={() =>
                  onSend({
                    type: "approval",
                    request_id: msg.request_id,
                    approved: false,
                  })
                }
              />
            );
          case "input":
            return (
              <UserInputWidget
                key={i}
                question={msg.question}
                options={msg.options}
                inputType={msg.input_type}
                resolved={msg.resolved}
                onSubmit={(value) =>
                  onSend({
                    type: "user_input",
                    request_id: msg.request_id,
                    value,
                  })
                }
              />
            );
          case "output":
            return (
              <TerminalOutput key={i} stream={msg.stream} text={msg.text} />
            );
        }
      })}

      <div ref={bottomRef} />
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ChatWindow.tsx
git commit -m "Add ChatWindow component"
```

---

### Task 17: App.tsx — Wire Everything Together

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Replace App.tsx**

Replace `frontend/src/App.tsx`:

```tsx
import { useCallback, useState } from "react";
import type { ChatMessage, ClientMessage, Phase, ServerMessage } from "./types";
import { useWebSocket } from "./hooks/useWebSocket";
import { UrlInput } from "./components/UrlInput";
import { StatusBar } from "./components/StatusBar";
import { ChatWindow } from "./components/ChatWindow";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [progress, setProgress] = useState<number | undefined>();
  const [started, setStarted] = useState(false);
  const [chatInput, setChatInput] = useState("");

  const handleMessage = useCallback((msg: ServerMessage) => {
    switch (msg.type) {
      case "agent_message":
        setMessages((prev) => [...prev, { kind: "agent", text: msg.text }]);
        break;
      case "approval_request":
        setMessages((prev) => [
          ...prev,
          {
            kind: "approval",
            request_id: msg.request_id,
            command: msg.command,
            description: msg.description,
          },
        ]);
        break;
      case "user_input_request":
        setMessages((prev) => [
          ...prev,
          {
            kind: "input",
            request_id: msg.request_id,
            question: msg.question,
            options: msg.options,
            input_type: msg.input_type,
          },
        ]);
        break;
      case "command_output":
        setMessages((prev) => [
          ...prev,
          { kind: "output", stream: msg.stream, text: msg.text },
        ]);
        break;
      case "status_update":
        setPhase(msg.phase as Phase);
        setStatusMessage(msg.message);
        setProgress(msg.progress);
        break;
      case "done":
        setPhase(msg.success ? "done" : "error");
        setStatusMessage(msg.message);
        break;
    }
  }, []);

  const { send, connected } = useWebSocket(handleMessage);

  const handleUrlSubmit = (url: string) => {
    setStarted(true);
    setPhase("scanning");
    setMessages([{ kind: "user", text: url }]);
    send({ type: "start", url });
  };

  const handleSend = (msg: ClientMessage) => {
    // Mark approval/input messages as resolved
    if (msg.type === "approval" || msg.type === "user_input") {
      setMessages((prev) =>
        prev.map((m) => {
          if (
            (m.kind === "approval" || m.kind === "input") &&
            m.request_id === msg.request_id
          ) {
            return { ...m, resolved: true };
          }
          return m;
        })
      );
    }
    send(msg);
  };

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setMessages((prev) => [...prev, { kind: "user", text: chatInput }]);
    send({ type: "message", text: chatInput });
    setChatInput("");
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">One-Click Repo</h1>
        <div
          className={`w-2 h-2 rounded-full ${
            connected ? "bg-green-500" : "bg-red-500"
          }`}
          title={connected ? "Connected" : "Disconnected"}
        />
      </header>

      <StatusBar phase={phase} message={statusMessage} progress={progress} />

      {!started && <UrlInput onSubmit={handleUrlSubmit} />}

      <ChatWindow messages={messages} onSend={handleSend} />

      {/* Chat input */}
      {started && (
        <form
          onSubmit={handleChatSubmit}
          className="flex gap-2 p-4 border-t border-gray-200"
        >
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!chatInput.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            Send
          </button>
        </form>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Clean up main.tsx**

Replace `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 3: Remove default Vite boilerplate files**

```bash
rm -f frontend/src/App.css frontend/src/assets/react.svg frontend/public/vite.svg
```

- [ ] **Step 4: Verify frontend builds**

```bash
cd /Users/kyle/projects/oc_repo/frontend
npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/kyle/projects/oc_repo
git add frontend/src/App.tsx frontend/src/main.tsx
git add -u  # pick up deleted boilerplate files
git commit -m "Wire up App with all components"
```

---

### Task 18: End-to-End Smoke Test

**Files:**
- Create: `.env` (from .env.example, with real API key)

- [ ] **Step 1: Create .env with your API key**

```bash
cp .env.example .env
# Edit .env to add your real LLM_API_KEY
```

- [ ] **Step 2: Start the backend**

In one terminal:
```bash
cd /Users/kyle/projects/oc_repo
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- [ ] **Step 3: Start the frontend**

In another terminal:
```bash
cd /Users/kyle/projects/oc_repo/frontend
npm run dev
```

- [ ] **Step 4: Open browser and test**

1. Open `http://localhost:5173`
2. Verify: URL input field is visible
3. Paste `https://github.com/kyusongy/OpenLecture`
4. Click "Go"
5. Verify: Agent starts scanning (status bar shows "Scanning")
6. Verify: Agent messages appear in chat
7. Verify: Approval cards appear for commands
8. Click "Approve" on each command
9. Verify: Terminal output appears
10. Verify: Agent launches the project

- [ ] **Step 5: Run all backend tests**

```bash
cd /Users/kyle/projects/oc_repo
uv run pytest tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "Complete v1 of One-Click Repo"
```
