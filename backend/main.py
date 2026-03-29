import asyncio
import os
import shutil
from dataclasses import asdict

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.engine import AgentEngine
from backend.agent.llm import get_client, get_model
from backend.projects import (
    load_projects,
    get_project,
    remove_project,
    refresh_statuses,
    save_projects,
)
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


@app.get("/api/projects")
async def list_projects():
    projects = load_projects()
    projects = await refresh_statuses(projects)
    save_projects(projects)  # persist updated statuses
    return [asdict(p) for p in projects]


@app.post("/api/projects/{name}/stop")
async def stop_project(name: str):
    project = get_project(name)
    if not project:
        raise HTTPException(404, "Project not found")
    for port in project.ports:
        proc = await asyncio.create_subprocess_shell(
            f"lsof -ti:{port} | xargs kill 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
    # Update status
    projects = load_projects()
    for p in projects:
        if p.name == name:
            p.status = "stopped"
    save_projects(projects)
    return {"status": "stopped"}


@app.delete("/api/projects/{name}")
async def delete_project(name: str):
    project = get_project(name)
    if not project:
        raise HTTPException(404, "Project not found")
    # Stop first
    for port in project.ports:
        proc = await asyncio.create_subprocess_shell(
            f"lsof -ti:{port} | xargs kill 2>/dev/null",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
    # Delete directory
    if os.path.exists(project.path):
        shutil.rmtree(project.path)
    # Remove from tracking
    remove_project(name)
    return {"status": "removed"}


@app.post("/api/projects/{name}/open")
async def open_project(name: str):
    project = get_project(name)
    if not project:
        raise HTTPException(404, "Project not found")
    if os.path.exists(project.path):
        proc = await asyncio.create_subprocess_exec("open", project.path)
        await proc.communicate()
    return {"status": "opened", "path": project.path}


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
        await ws.send_json(
            {"type": "agent_message", "text": f"Configuration error: {e}"}
        )
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
                relaunch_path = data.get("path")
                if relaunch_path:
                    user_msg = f"Please relaunch the project at {relaunch_path}. It was installed from {url}. Check what services need to start and launch them."
                else:
                    user_msg = f"Please install this GitHub repository: {url}"
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
