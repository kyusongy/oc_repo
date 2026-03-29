import argparse
import asyncio
import json
import sys
import uuid

from dotenv import load_dotenv

from backend.agent.engine import AgentEngine
from backend.agent.llm import get_client, get_model
from backend.tools import create_registry


def log(msg: str = ""):
    """Print with immediate flush."""
    print(msg, flush=True)


class CliSession:
    """Terminal-based session that replaces WebSocket communication."""

    def __init__(self, auto_approve: bool = False, verbose: bool = False):
        self.auto_approve = auto_approve
        self.verbose = verbose
        self._pending: dict[str, asyncio.Future] = {}

    async def send(self, msg: dict):
        """Handle messages that would normally go to the frontend via WebSocket."""
        msg_type = msg.get("type")

        if msg_type == "approval_request":
            request_id = msg["request_id"]
            command = msg["command"]
            description = msg["description"]

            log(f"\n{'=' * 60}")
            log("APPROVAL REQUIRED")
            log(f"   {description}")
            log(f"   Command: {command}")
            log(f"{'=' * 60}")

            if self.auto_approve:
                log("   Auto-approved")
                approved = True
            else:
                response = input("   Approve? [y/N]: ").strip().lower()
                approved = response in ("y", "yes")
                log(f"   {'Approved' if approved else 'Denied'}")

            future = self._pending.pop(request_id, None)
            if future and not future.done():
                future.set_result(approved)

        elif msg_type == "user_input_request":
            request_id = msg["request_id"]
            question = msg["question"]
            input_type = msg.get("input_type", "text")
            options = msg.get("options")

            log(f"\n{'=' * 60}")
            log(f"? {question}")

            if self.auto_approve:
                if options and input_type == "choice":
                    value = options[0]["label"]
                else:
                    value = "SKIPPED_IN_AUTO_MODE"
                log(f"   Auto-response: {value}")
            elif options and input_type == "choice":
                for i, opt in enumerate(options, 1):
                    log(f"   {i}. {opt['label']} -- {opt.get('description', '')}")
                choice = input("   Choose (number): ").strip()
                try:
                    idx = int(choice) - 1
                    value = options[idx]["label"]
                except (ValueError, IndexError):
                    value = choice
            elif input_type == "password":
                try:
                    import getpass

                    value = getpass.getpass("   Enter value (hidden): ")
                except (EOFError, OSError):
                    value = input("   Enter value: ").strip()
            else:
                value = input("   Your answer: ").strip()

            log(f"{'=' * 60}")

            future = self._pending.pop(request_id, None)
            if future and not future.done():
                future.set_result(value)

        elif msg_type == "command_output":
            stream = msg["stream"]
            text = msg["text"]
            prefix = "[stdout]" if stream == "stdout" else "[stderr]"
            lines = text.split("\n")
            if len(lines) > 20 and not self.verbose:
                log(f"\n{prefix} ({len(lines)} lines, showing first/last 5)")
                for line in lines[:5]:
                    log(f"   {line}")
                log(f"   ... ({len(lines) - 10} lines omitted) ...")
                for line in lines[-5:]:
                    log(f"   {line}")
            else:
                log(f"\n{prefix}")
                for line in lines:
                    log(f"   {line}")

        elif msg_type == "status_update":
            phase = msg["phase"]
            message = msg["message"]
            progress = msg.get("progress")
            prog = f" ({progress:.0f}%)" if progress is not None else ""
            log(f"\n[{phase.upper()}]{prog} {message}")

        elif self.verbose:
            log(f"\n[DEBUG] {json.dumps(msg, indent=2)}")

    async def request_approval(self, command: str, description: str) -> bool:
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        await self.send(
            {
                "type": "approval_request",
                "request_id": request_id,
                "command": command,
                "description": description,
            }
        )
        return await future

    async def request_input(
        self, question: str, options=None, input_type: str = "text"
    ) -> str:
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        msg = {
            "type": "user_input_request",
            "request_id": request_id,
            "question": question,
            "input_type": input_type,
        }
        if options:
            msg["options"] = options
        await self.send(msg)
        return await future

    async def send_output(self, stream: str, text: str):
        await self.send({"type": "command_output", "stream": stream, "text": text})

    async def send_status(self, phase: str, message: str, progress=None):
        msg = {"type": "status_update", "phase": phase, "message": message}
        if progress is not None:
            msg["progress"] = progress
        await self.send(msg)

    def resolve(self, request_id: str, value):
        future = self._pending.pop(request_id, None)
        if future and not future.done():
            future.set_result(value)


async def main():
    parser = argparse.ArgumentParser(description="One-Click Repo CLI")
    parser.add_argument("url", help="GitHub repository URL to install")
    parser.add_argument(
        "--auto-approve", action="store_true", help="Auto-approve all commands"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show raw tool calls/results"
    )
    args = parser.parse_args()

    load_dotenv()

    try:
        client = get_client()
        model = get_model()
    except ValueError as e:
        log(f"Configuration error: {e}")
        log("   Make sure .env has LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL")
        sys.exit(1)

    log("One-Click Repo CLI")
    log(f"   Model: {model}")
    log(f"   URL: {args.url}")
    log(f"   Auto-approve: {args.auto_approve}")
    log(f"{'=' * 60}\n")

    session = CliSession(auto_approve=args.auto_approve, verbose=args.verbose)
    registry = create_registry()
    engine = AgentEngine(client, model, registry, session)

    history: list[dict] = []
    user_msg = f"Please install this GitHub repository: {args.url}"

    log(f"User: {user_msg}\n")

    try:
        while True:
            async for text in engine.run(user_msg, history):
                log(f"\nAgent: {text}\n")

            if args.auto_approve:
                break

            try:
                user_msg = input("You (or 'q' to quit): ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_msg or user_msg.lower() == "q":
                break
            log()
    except KeyboardInterrupt:
        log("\n\nInterrupted by user")
    except Exception as e:
        log(f"\nError: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    log(f"\n{'=' * 60}")
    log("Done!")


if __name__ == "__main__":
    asyncio.run(main())
