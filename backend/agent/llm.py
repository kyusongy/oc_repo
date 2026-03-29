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


async def chat(
    client: AsyncOpenAI, model: str, messages: list[dict], tools: list[dict]
):
    kwargs = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return await client.chat.completions.create(**kwargs)
