import os

import httpx
from dotenv import load_dotenv

from cost_control.limit import check_spend_limit
from cost_control.recorder import record_usage

load_dotenv()

openrouter_url = "https://openrouter.ai/api/v1/chat/completions"


def send_to_llm(messages, timeout_seconds):
    # Check if the daily spend limit has been reached
    check_spend_limit()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    model_name = os.environ.get("OPENROUTER_MODEL")

    headers = {"Authorization": f"Bearer {api_key}"}

    body = {
        "model": model_name,
        "temperature": 0,
        "messages": messages,
    }

    response = httpx.post(openrouter_url, headers=headers, json=body, timeout=timeout_seconds)
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


def ask_llm(system_instruction, user_text):
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_text},
    ]
    return send_to_llm(messages, 60)


def ask_llm_with_pictures(system_instruction, picture_links):
    picture_detail = os.environ.get("OCR_IMAGE_DETAIL", "low")

    user_parts = []
    for picture_link in picture_links:
        picture_part = {
            "type": "image_url",
            "image_url": {"url": picture_link, "detail": picture_detail},
        }
        user_parts.append(picture_part)

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_parts},
    ]
    return send_to_llm(messages, 120)