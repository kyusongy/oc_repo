# One-Click Repo (oc_repo) — Design Spec

## Overview

An LLM-powered agent that helps non-technical users install and run any GitHub repository on their Mac by pasting a URL into a conversational web interface. The agent scans the repo, assesses feasibility, guides the user through setup, auto-diagnoses errors, and launches the project.

**Context:** STOR 522 course project (4-person team). Professor confirmed LLM API-based agentic systems qualify as "end-to-end ML system."

**Demo plan:** Live installation of [OpenLecture](https://github.com/kyusongy/OpenLecture) during the 15-minute final presentation.

## Target User

Non-technical person who found a cool GitHub repo (on Twitter, Reddit, etc.) and wants to run it locally. They don't know git, terminal, or dependency management. The agent bridges that gap.

## Architecture

### System Overview

```
React Frontend (Chat UI)
    ↕ WebSocket (streaming)
FastAPI Backend (Agent Engine + Tools)
    ↕ OpenAI-compatible API
LLM Provider (configurable via env)
```

### Components

1. **React Frontend** — Chat interface with message bubbles, command approval cards, structured input widgets (text, password, choice), terminal output viewer, and status indicators. Connected to backend via WebSocket for real-time streaming.

2. **FastAPI Backend** — Hosts the agent loop. Receives user messages via WebSocket, runs the LLM tool-use loop, executes tool calls, streams results back to the frontend.

3. **Agent Engine** — A loop that sends messages + tool definitions to the LLM, receives tool calls, executes them, and feeds results back until the LLM responds with text. All orchestration intelligence lives in the LLM, not in application code.

4. **Tool Registry** — Python functions the agent can call. Each tool has a name, description, JSON schema for parameters, and an execute method.

5. **LLM Client** — Single OpenAI-compatible client. Configurable via environment variables:
   ```
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=sk-...
   LLM_MODEL=gpt-5.4
   ```

## Tools

### Tool Definitions

| Tool | Purpose | Approval | Auto/Manual |
|------|---------|----------|-------------|
| `clone_repo` | Clone a GitHub repo to local directory | Auto | Auto |
| `list_files` | List files in a directory with optional glob pattern | Auto | Auto |
| `read_file` | Read file contents (with max_lines to avoid context overflow) | Auto | Auto |
| `run_command` | Execute a shell command (the core capability) | **User approves** | Manual |
| `check_system` | Detect OS, installed tools, RAM, disk, etc. | Auto | Auto |
| `ask_user` | Ask the user a question with optional structured input | N/A | Manual |
| `report_status` | Update the UI status indicator | Auto | Auto |

### Tool Interfaces

```python
class Tool(ABC):
    name: str
    description: str          # Sent to LLM
    parameters: dict          # JSON Schema
    requires_approval: bool

    @abstractmethod
    async def execute(self, params: dict) -> ToolResult

@dataclass
class ToolResult:
    output: str              # What the LLM sees
    success: bool
    ui_payload: dict | None  # Extra data for frontend rendering
```

### `run_command` — Critical Tool

```
Input:  { command: str, cwd?: str, description: str }
Output: { stdout: str, stderr: str, exit_code: int, timed_out: bool }
```

- `description` is mandatory — the LLM must explain what the command does in plain English. This becomes the approval prompt.
- Always requires user approval (v1).
- Streams stdout/stderr to frontend via WebSocket in real-time.
- 5-minute timeout per command.
- Default working directory: `~/oc_repo_workspace/<repo-name>/` — keeps cloned repos organized and isolated from the user's own files.

### `ask_user` — Interactive Widget Tool

```
Input:  { question: str, options?: [{label, description}], input_type?: "choice"|"text"|"password" }
Output: { answer: str }
```

- Renders inline UI widgets in the chat (buttons for choices, text field, masked input for passwords/API keys).
- Blocks the agent loop until the user responds.

## Agent Behavior

### Three Phases (Single Agent, Single Conversation)

No separate agents — one LLM handles all phases. The system prompt guides behavior.

#### Phase 1: Scan & Assess

1. `check_system()` — learn the user's machine capabilities
2. `clone_repo(url)` — clone the repository
3. `list_files()` + `read_file()` on README, config files (package.json, requirements.txt, Dockerfile, setup.py, etc.)
4. Agent synthesizes a feasibility assessment and presents it conversationally:
   > "This is a Python web app using Flask and PostgreSQL. You have Python 3.11 ✓ but PostgreSQL is missing ✗. It also needs an OpenAI API key. Want me to proceed?"
5. If infeasible (needs GPU, specific OS, heavy hardware the user lacks), agent explains why and stops.

#### Phase 2: Install & Configure

1. Agent determines installation steps from what it learned in Phase 1
2. Each step uses `run_command` with a plain-English description
3. User approves each command via the approval card UI
4. On failure: agent reads stderr, diagnoses the issue, and retries with a fix (max 3 retries per step)
5. When credentials/config are needed, agent uses `ask_user` with appropriate input type
6. Agent writes `.env` files or config files as needed via `run_command`

#### Phase 3: Launch & Verify

1. Agent runs the start command (e.g., `python app.py`, `npm start`)
2. If it's a web app, agent tells user to open `localhost:XXXX`
3. Agent checks for "it's running" signals (port open, no crash in first 5 seconds)
4. Final message: "Your project is running! Open http://localhost:3000 in your browser."

### System Prompt

```
You are One-Click Repo, a friendly installation assistant.
Your job: help non-technical users install and run GitHub projects on their computer.

Rules:
- Explain everything in plain, non-technical language
- Always describe what a command does BEFORE running it (use the description field)
- If something fails, diagnose the error and try to fix it (max 3 retries per step)
- If you can't fix it, explain the problem honestly in simple terms
- Never run destructive commands (rm -rf, format, etc.)
- Ask the user before doing anything that requires credentials or costs money
- Start by checking the user's system, then clone and analyze the repo

You have access to these tools: [tool schemas injected here]
```

## Frontend Design

### Layout

```
┌──────────────────────────────────────────────┐
│  One-Click Repo                        [⚙]  │
├──────────────────────────────────────────────┤
│  [Status Bar: Scanning → Installing → Done]  │
├──────────────────────────────────────────────┤
│                                              │
│  URL Input: [Paste GitHub URL]  [Go]         │
│                                              │
│  Chat Messages:                              │
│  - Agent messages (markdown rendered)        │
│  - Command approval cards (command + desc    │
│    + approve/deny buttons)                   │
│  - User input widgets (inline text/password/ │
│    choice rendered from ask_user tool)       │
│  - Terminal output (collapsible, raw output) │
│                                              │
├──────────────────────────────────────────────┤
│  [Type a message...]                 [Send]  │
└──────────────────────────────────────────────┘
```

### UI Components

1. **UrlInput** — prominent input field + Go button. Entry point.
2. **ChatWindow** — scrollable message list.
3. **MessageBubble** — agent and user messages. Agent messages render markdown.
4. **ApprovalCard** — command + plain English description + Approve/Deny buttons.
5. **UserInputWidget** — rendered inline when `ask_user` fires. Supports text, password (masked), and multiple choice.
6. **TerminalOutput** — collapsible panel showing raw stdout/stderr from commands.
7. **StatusBar** — top bar showing current phase and progress.

### Tech Stack

- React + TypeScript
- WebSocket via native browser API
- Tailwind CSS
- Vite for dev/build

## Data Flow

### WebSocket Message Protocol

```typescript
// Frontend → Backend
{ type: "start", url: string }
{ type: "message", text: string }
{ type: "approval", request_id: string, approved: boolean }
{ type: "user_input", request_id: string, value: string }

// Backend → Frontend
{ type: "agent_message", text: string }
{ type: "approval_request", request_id: string, command: string, description: string }
{ type: "user_input_request", request_id: string, question: string, options?: Array, input_type: string }
{ type: "command_output", stream: "stdout"|"stderr", text: string }
{ type: "status_update", phase: string, message: string, progress?: number }
{ type: "done", success: boolean, message: string }
```

### Agent Loop

```python
async def agent_loop(messages, tools):
    while True:
        response = await llm.chat(messages, tools)

        if response.is_text:
            yield AgentMessage(response.text)
            return

        for tool_call in response.tool_calls:
            tool = registry[tool_call.name]

            if tool.requires_approval:
                approved = await request_approval(tool_call)  # WebSocket → UI → user
                if not approved:
                    messages.append(tool_result(tool_call.id, "User denied this action"))
                    continue

            result = await tool.execute(tool_call.params)
            messages.append(tool_result(tool_call.id, result.output))
```

## Error Handling

| Error Type | Strategy |
|-----------|----------|
| Command failure | Agent reads stderr, diagnoses, retries with fix (max 3 retries) |
| LLM API failure | Exponential backoff, 3 retries, then friendly error to user |
| Clone failure | Check URL validity, repo visibility, network. Report clearly. |
| Command timeout | 5-minute timeout. Agent informs user, suggests alternatives. |
| Unrecoverable | Agent explains in plain English, suggests manual steps if possible. |

## Project Structure

```
oc_repo/
├── backend/
│   ├── main.py                 # FastAPI app, WebSocket endpoint
│   ├── agent/
│   │   ├── engine.py           # Agent loop (LLM ↔ tools cycle)
│   │   ├── prompt.py           # System prompt
│   │   └── llm.py              # OpenAI-compatible client config
│   ├── tools/
│   │   ├── base.py             # Tool ABC, ToolResult
│   │   ├── clone_repo.py
│   │   ├── read_file.py
│   │   ├── list_files.py
│   │   ├── run_command.py
│   │   ├── check_system.py
│   │   ├── ask_user.py
│   │   └── report_status.py
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ApprovalCard.tsx
│   │   │   ├── UserInputWidget.tsx
│   │   │   ├── TerminalOutput.tsx
│   │   │   ├── StatusBar.tsx
│   │   │   └── UrlInput.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── types.ts
│   ├── package.json
│   └── tailwind.config.js
├── pyproject.toml              # uv project config (backend deps)
├── uv.lock
├── .env.example
└── README.md
```

## Scope — v1 (Course Project)

**In scope:**
- Mac only
- Any public GitHub repo with a README
- Single agent with tool-use architecture
- Conversational chat UI with approval cards and input widgets
- Pre-scan with feasibility assessment
- Command-by-command installation with user approval
- Auto-diagnosis and retry on failures (max 3)
- Launch the project after successful install
- Configurable LLM via OpenAI-compatible API (base URL + key + model)

**Out of scope (future):**
- Windows/Linux support
- Private repo authentication
- Desktop app (Electron/Tauri)
- Sandbox/container isolation
- Repo browsing/discovery
- Ongoing help after launch
- Multiple concurrent installations
