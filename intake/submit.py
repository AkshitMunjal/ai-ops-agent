import os

import httpx

agent_api_url = os.environ.get("AGENT_API_URL", "http://127.0.0.1:8001")


class TryLaterError(Exception):
    pass


def submit_email_text(email_text, message_id=None):
    response = httpx.post(
        agent_api_url + "/runs",
        json={"email_text": email_text, "message_id": message_id},
        timeout=120,
    )

    if response.status_code == 429:
        detail = response.json().get("detail", "The agent API asked us to try again later")
        raise TryLaterError(detail)

    response.raise_for_status()

    run = response.json()
    run["already_seen"] = response.status_code == 200
    return run