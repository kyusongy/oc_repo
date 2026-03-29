import asyncio

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
