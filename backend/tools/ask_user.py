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
        self.session = None

    async def execute(self, params: dict) -> ToolResult:
        if not self.session:
            return ToolResult(output="Error: no session available", success=False)

        question = params["question"]
        options = params.get("options")
        input_type = params.get("input_type", "text")

        answer = await self.session.request_input(question, options, input_type)
        return ToolResult(output=answer, success=True)
