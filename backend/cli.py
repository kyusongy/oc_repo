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

    def __init__(
        self,
        auto_approve: bool = False,
        verbose: bool = False,
        default_input: str | None = None,
    ):
        self.auto_approve = auto_approve
        self.verbose = verbose
        self.default_input = default_input
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
                elif self.default_input:
                    value = self.default_input
                else:
                    value = "SKIPPED_IN_AUTO_MODE"
                display = (
                    value[:8] + "..."
                    if input_type == "password" and len(value) > 8
                    else value
                )
                log(f"   Auto-response: {display}")
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


async def cmd_install(args):
    """Install a GitHub repo."""
    load_dotenv()
    client = get_client()
    model = get_model()

    log("One-Click Repo CLI")
    log(f"   Model: {model}")
    log(f"   URL: {args.url}")
    log(f"   Mode: {'auto' if args.auto_approve else 'safe'}")
    log(f"{'=' * 60}\n")

    session = CliSession(
        auto_approve=args.auto_approve,
        verbose=args.verbose,
        default_input=args.default_input,
    )
    registry = create_registry()
    engine = AgentEngine(client, model, registry, session, auto_mode=args.auto_approve)

    history = []
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
        log("\n\nInterrupted")
    except Exception as e:
        log(f"\nError: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


async def cmd_list(args):
    """List installed projects."""
    from backend.projects import load_projects_with_auto_detect, refresh_statuses

    projects = load_projects_with_auto_detect()
    projects = await refresh_statuses(projects)

    if not projects:
        log("No projects found in workspace.")
        return

    log(f"{'Name':<25} {'Status':<10} {'Ports':<15} {'URL'}")
    log("-" * 80)
    for p in projects:
        ports = ", ".join(str(port) for port in p.ports) if p.ports else "-"
        url = p.url or "(auto-detected)"
        log(f"{p.name:<25} {p.status:<10} {ports:<15} {url}")


async def cmd_stop(args):
    """Stop a running project."""
    from backend.projects import (
        load_projects,
        save_projects,
        load_projects_with_auto_detect,
    )

    projects = load_projects()
    project = next((p for p in projects if p.name == args.name), None)

    if not project:
        # Check auto-detected
        all_projects = load_projects_with_auto_detect()
        project = next((p for p in all_projects if p.name == args.name), None)

    if not project:
        log(f"Project '{args.name}' not found.")
        sys.exit(1)

    if not project.ports:
        log(f"No ports tracked for '{args.name}'. Nothing to stop.")
        return

    import os

    my_pid = os.getpid()
    for port in project.ports:
        proc = await asyncio.create_subprocess_shell(
            f"lsof -ti:{port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        for pid_str in stdout.decode().strip().split("\n"):
            if not pid_str:
                continue
            try:
                pid = int(pid_str)
            except ValueError:
                continue
            if pid != my_pid:
                try:
                    os.kill(pid, 15)
                    log(f"Killed PID {pid} on port {port}")
                except ProcessLookupError:
                    pass

    # Update status
    projects = load_projects()
    for p in projects:
        if p.name == args.name:
            p.status = "stopped"
    save_projects(projects)
    log(f"Stopped '{args.name}'")


async def cmd_remove(args):
    """Stop and remove a project."""
    import os
    import shutil
    from backend.projects import remove_project, load_projects_with_auto_detect

    all_projects = load_projects_with_auto_detect()
    project = next((p for p in all_projects if p.name == args.name), None)

    if not project:
        log(f"Project '{args.name}' not found.")
        sys.exit(1)

    if not args.force:
        confirm = (
            input(f"Remove '{args.name}' and delete {project.path}? [y/N]: ")
            .strip()
            .lower()
        )
        if confirm not in ("y", "yes"):
            log("Cancelled.")
            return

    # Stop first
    if project.ports:
        await cmd_stop(type("Args", (), {"name": args.name})())

    # Delete directory
    if os.path.exists(project.path):
        shutil.rmtree(project.path)
        log(f"Deleted {project.path}")

    remove_project(args.name)
    log(f"Removed '{args.name}'")


async def cmd_history(args):
    """Show installation history for a project."""
    from backend.projects import load_history, load_projects_with_auto_detect

    all_projects = load_projects_with_auto_detect()
    project = next((p for p in all_projects if p.name == args.name), None)

    if not project:
        log(f"Project '{args.name}' not found.")
        sys.exit(1)

    history = load_history(project.path)
    if not history:
        log(f"No history found for '{args.name}'.")
        return

    log(f"Session history for '{args.name}' ({len(history)} messages):\n")
    for msg in history:
        kind = msg.get("kind", "?")
        if kind == "agent":
            log(
                f"Agent: {msg['text'][:200]}{'...' if len(msg.get('text', '')) > 200 else ''}\n"
            )
        elif kind == "user":
            log(f"User: {msg['text']}\n")
        elif kind == "auto_approved":
            log(f"  [auto] {msg.get('description', '')} — {msg.get('command', '')}")
        elif kind == "approval":
            resolved = "approved" if msg.get("resolved") else "pending"
            log(
                f"  [approval:{resolved}] {msg.get('description', '')} — {msg.get('command', '')}"
            )
        elif kind == "output":
            lines = msg.get("text", "").split("\n")
            log(f"  [{msg.get('stream', 'output')}] ({len(lines)} lines)")


async def main():
    parser = argparse.ArgumentParser(description="One-Click Repo CLI")
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # install
    p_install = sub.add_parser("install", help="Install a GitHub repository")
    p_install.add_argument("url", help="GitHub repository URL")
    p_install.add_argument(
        "--auto-approve", action="store_true", help="Auto-approve safe commands"
    )
    p_install.add_argument(
        "--default-input", default=None, help="Default value for user input prompts"
    )
    p_install.add_argument("--verbose", action="store_true")

    # list
    sub.add_parser("list", help="List installed projects")

    # stop
    p_stop = sub.add_parser("stop", help="Stop a running project")
    p_stop.add_argument("name", help="Project name")

    # remove
    p_remove = sub.add_parser("remove", help="Remove an installed project")
    p_remove.add_argument("name", help="Project name")
    p_remove.add_argument("--force", action="store_true", help="Skip confirmation")

    # history
    p_history = sub.add_parser("history", help="Show installation history")
    p_history.add_argument("name", help="Project name")

    args = parser.parse_args()

    if args.command == "install":
        await cmd_install(args)
    elif args.command == "list":
        await cmd_list(args)
    elif args.command == "stop":
        await cmd_stop(args)
    elif args.command == "remove":
        await cmd_remove(args)
    elif args.command == "history":
        await cmd_history(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
