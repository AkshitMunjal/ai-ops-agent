import os

import httpx
from dotenv import load_dotenv

from cost_control.limit import check_spend_limit
from cost_control.recorder import record_usage

load_dotenv()

openrouter_url = "https://openrouter.ai/api/v1/chat/completions"


class ChatLlmError(Exception):
    """The AI service failed or gave an unexpected answer."""


def ask_llm_with_tools(messages, tools):
    """Send the conversation and the tool list. Returns the assistant message."""
    # Stops with SpendLimitReached if the daily limit is used up.
    check_spend_limit()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")

    headers = {"Authorization": f"Bearer {api_key}"}
    body = {
        "model": model_name,
        "temperature": 0,
        "messages": messages,
        "tools": tools,
    }

    try:
        response = httpx.post(openrouter_url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise ChatLlmError(f"The AI service failed: {error}") from error

    data = response.json()

    usage = data.get("usage") or {}
    try:
        record_usage(model_name, usage)
    except Exception as error:
        print(f"Could not save the LLM usage: {error}")

    choices = data.get("choices")
    if not choices:
        raise ChatLlmError("The AI service answered without any choices.")

    return choices[0]["message"]
