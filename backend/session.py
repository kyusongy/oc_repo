import asyncio
import uuid


class Session:
    """Manages WebSocket communication between tools and the frontend."""

    def __init__(self, send_fn):
        self.send = send_fn
        self._pending: dict[str, asyncio.Future] = {}

    async def request_approval(self, command: str, description: str) -> bool:
        request_id = str(uuid.uuid4())
        await self.send(
            {
                "type": "approval_request",
                "request_id": request_id,
                "command": command,
                "description": description,
            }
        )
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
        await self.send(
            {
                "type": "command_output",
                "stream": stream,
                "text": text,
            }
        )

    async def send_status(
        self, phase: str, message: str, progress: float | None = None
    ):
        msg = {"type": "status_update", "phase": phase, "message": message}
        if progress is not None:
            msg["progress"] = progress
        await self.send(msg)

    def resolve(self, request_id: str, value):
        future = self._pending.pop(request_id, None)
        if future and not future.done():
            future.set_result(value)
