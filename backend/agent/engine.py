import json

from openai import AsyncOpenAI

from backend.agent.prompt import SYSTEM_PROMPT
from backend.agent.safety import classify_command
from backend.session import Session
from backend.tools.base import ToolRegistry


class AgentEngine:
    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        registry: ToolRegistry,
        session: Session | None = None,
        auto_mode: bool = False,
    ):
        self.client = client
        self.model = model
        self.registry = registry
        self.session = session
        self.auto_mode = auto_mode

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
                history.append(
                    {
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
                    }
                )

                for tc in message.tool_calls:
                    tool_name = tc.function.name
                    arguments = json.loads(tc.function.arguments)

                    tool = self.registry.get(tool_name)

                    if hasattr(tool, "session") and self.session:
                        tool.session = self.session

                    if self.session:
                        desc = arguments.get("description", tool_name)
                        await self.session.send(
                            {
                                "type": "tool_start",
                                "tool_name": tool_name,
                                "description": desc,
                            }
                        )

                    # Handle approval for tools that require it
                    if tool.requires_approval and self.session:
                        command = arguments.get("command", str(arguments))
                        description = arguments.get("description", tool_name)
                        approved = True

                        if self.auto_mode:
                            safety = await classify_command(
                                command, self.client, self.model
                            )
                            if safety == "safe":
                                await self.session.send(
                                    {
                                        "type": "auto_approved",
                                        "command": command,
                                        "description": description,
                                    }
                                )
                            elif safety == "dangerous":
                                history.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tc.id,
                                        "content": "Command blocked: classified as dangerous.",
                                    }
                                )
                                continue
                            else:
                                approved = await self.session.request_approval(
                                    command, description
                                )
                        else:
                            approved = await self.session.request_approval(
                                command, description
                            )

                        if not approved:
                            history.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tc.id,
                                    "content": "User denied this action.",
                                }
                            )
                            continue

                    result = await tool.execute(arguments)

                    if tool_name == "run_command" and self.session:
                        await self.session.send_output("stdout", result.output)

                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result.output,
                        }
                    )
            else:
                # LLM responded with text — yield to frontend
                text = message.content or ""
                history.append({"role": "assistant", "content": text})
                yield text
                return
