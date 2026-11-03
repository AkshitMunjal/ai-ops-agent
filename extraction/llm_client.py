import os

import httpx
from dotenv import load_dotenv

from cost_control.limit import check_spend_limit
from cost_control.recorder import record_usage

load_dotenv()

openrouter_url = "https://openrouter.ai/api/v1/chat/completions"


def ask_llm(system_instruction, user_text):

    # Check if the daily spend limit has been reached
    check_spend_limit()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")

    headers = {"Authorization": f"Bearer {api_key}"}

    body = {
        "model": model_name,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_text},
        ],
    }

    response = httpx.post(openrouter_url, headers=headers, json=body, timeout=60)
    response.raise_for_status()

    data = response.json()

    usage = data.get("usage") or {}
    try:
        record_usage(model_name, usage)
    except Exception as error:
        print(f"Could not save the LLM usage: {error}")

    choices = data["choices"]
    first_choice = choices[0]
    message = first_choice["message"]
    return message["content"]