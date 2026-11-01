from tests.test_agent_api import agent_client
from tests.test_agent_graph import install_fakes


def post_email_with_id(agent_client, message_id):
    return agent_client.post(
        "/runs",
        json={"email_text": "any email", "message_id": message_id},
    )


def test_same_message_id_twice_creates_only_one_run(agent_client, monkeypatch):
    calls = install_fakes(monkeypatch)

    first = post_email_with_id(agent_client, "<a@example.com>")
    second = post_email_with_id(agent_client, "<a@example.com>")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert len(calls["create"]) == 1
    assert len(agent_client.get("/runs").json()) == 1


def test_different_message_ids_create_separate_runs(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    first = post_email_with_id(agent_client, "<a@example.com>")
    second = post_email_with_id(agent_client, "<b@example.com>")

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]


def test_without_a_message_id_every_email_creates_a_run(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    first = agent_client.post("/runs", json={"email_text": "any email"})
    second = agent_client.post("/runs", json={"email_text": "any email"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert len(agent_client.get("/runs").json()) == 2


def test_the_repeated_email_returns_the_same_waiting_run(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    post_email_with_id(agent_client, "<a@example.com>")
    repeated = post_email_with_id(agent_client, "<a@example.com>")

    body = repeated.json()
    assert body["status"] == "waiting_for_approval"
    assert body["draft_order_id"] == 7