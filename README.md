# One-Click Repo

An LLM-powered agent that helps non-technical users install and run any GitHub repository by pasting a URL. The agent scans the repo, assesses feasibility, guides through setup, auto-diagnoses errors, and launches the project.

## How It Works

1. User pastes a GitHub URL
2. Agent checks the system for installed tools (git, python, node, etc.)
3. Agent clones the repo and reads its README and config files
4. Agent assesses feasibility — if the repo needs something the user doesn't have, it explains why
5. Agent installs dependencies step-by-step, asking permission before each command
6. Agent launches the project and confirms it's running

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 18+
- An OpenAI-compatible LLM API key

### Setup

```bash
git clone https://github.com/kyusongy/oc_repo.git
cd oc_repo

# Backend
uv sync
cp .env.example .env
# Edit .env with your API key and model

# Frontend
cd frontend
npm install
cd ..
```

### Configure `.env`

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
```

Any OpenAI-compatible API works — just change the base URL.

### Run (Web UI)

Terminal 1:
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2:
```bash
cd frontend
npm run dev
```

Open http://localhost:5173, paste a GitHub URL, and go.

### Run (CLI)

```bash
# Interactive mode
uv run python -m backend.cli https://github.com/user/repo

# Auto-approve all commands
uv run python -m backend.cli --auto-approve https://github.com/user/repo

# Pre-fill API keys for automated testing
uv run python -m backend.cli --auto-approve --default-input "sk-your-key" https://github.com/user/repo
```

## Architecture

```
React Frontend (Chat UI)
    ↕ WebSocket (streaming)
FastAPI Backend (Agent Engine + Tools)
    ↕ OpenAI-compatible API
LLM Provider (configurable)
```

Single-agent with tool-use. The LLM decides what to do — the tools are dumb executors.

### Tools

| Tool | Purpose |
|------|---------|
| `check_system` | Detect OS, installed tools, RAM, disk |
| `clone_repo` | Clone a GitHub repo |
| `list_files` | List directory contents with glob filtering |
| `read_file` | Read file contents |
| `run_command` | Execute shell commands (requires user approval) |
| `ask_user` | Ask the user for input (API keys, choices) |
| `report_status` | Update the UI status bar |

## Project Structure

```
oc_repo/
├── backend/
│   ├── main.py          # FastAPI WebSocket server
│   ├── cli.py           # CLI interface
│   ├── session.py       # WebSocket session management
│   ├── agent/
│   │   ├── engine.py    # LLM ↔ tools loop
│   │   ├── llm.py       # OpenAI-compatible client
│   │   └── prompt.py    # System prompt
│   └── tools/           # 7 tools (check_system, clone_repo, etc.)
├── frontend/
│   └── src/
│       ├── App.tsx       # Main app wiring
│       ├── types.ts      # WebSocket message types
│       ├── hooks/        # useWebSocket
│       └── components/   # Chat UI components
├── tests/               # 29 tests
├── pyproject.toml
└── .env.example
```

## Tests

```bash
uv run pytest tests/ -v
```
