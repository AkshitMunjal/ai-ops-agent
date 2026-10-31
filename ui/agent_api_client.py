import os

import httpx

agent_api_url = os.environ.get("AGENT_API_URL", "http://127.0.0.1:8001")


def get_runs(status):
    response = httpx.get(agent_api_url + "/runs", params={"status": status})
    response.raise_for_status()
    runs = response.json()
    return runs


def get_run_detail(run_id):
    response = httpx.get(agent_api_url + "/runs/" + str(run_id))
    response.raise_for_status()
    run_detail = response.json()
    return run_detail


def send_decision(run_id, decision):
    response = httpx.post(
        agent_api_url + "/runs/" + str(run_id) + "/decision",
        json={"decision": decision},
    )
    response.raise_for_status()
    updated_run = response.json()
    return updated_run


def dismiss_run(run_id):
    response = httpx.post(agent_api_url + "/runs/" + str(run_id) + "/dismiss")
    response.raise_for_status()
    dismissed_run = response.json()
    return dismissed_run