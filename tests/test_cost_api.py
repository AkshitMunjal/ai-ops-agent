from cost_control.limit import SpendLimitReached
from tests.test_agent_api import agent_client
from tests.test_agent_graph import install_fakes


def limit_reached():
    raise SpendLimitReached("Daily spend limit of $1 reached (spent $1.0000 today)")


def test_a_new_email_gets_429_when_the_limit_is_reached(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    monkeypatch.setattr("agent_api.routes.runs.check_spend_limit", limit_reached)

    response = agent_client.post("/runs", json={"email_text": "Please send 5 bolts"})

    assert response.status_code == 429
    assert "Daily spend limit" in response.json()["detail"]
    assert agent_client.get("/runs").json() == []


def test_an_already_handled_email_still_gets_its_answer_at_the_limit(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    body = {"email_text": "Please send 5 bolts", "message_id": "<same@example.com>"}

    first = agent_client.post("/runs", json=body)
    assert first.status_code == 201

    monkeypatch.setattr("agent_api.routes.runs.check_spend_limit", limit_reached)
    second = agent_client.post("/runs", json=body)

    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]