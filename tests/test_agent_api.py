import pytest
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from agent.graph import build_graph
from agent_api.create_tables import create_agent_tables
from agent_api.database import Base, database_engine
from agent_api.main import app
from tests.test_agent_graph import fake_match_with_problem, install_fakes


@pytest.fixture
def agent_client(monkeypatch):
    fresh_graph = build_graph(InMemorySaver())
    monkeypatch.setattr("agent_api.routes.runs.graph", fresh_graph)

    Base.metadata.drop_all(database_engine)
    create_agent_tables()

    return TestClient(app)


def post_email(agent_client):
    return agent_client.post("/runs", json={"email_text": "any email"})


def test_new_email_waits_for_approval(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    response = post_email(agent_client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "waiting_for_approval"
    assert body["draft_order_id"] == 7


def test_empty_email_is_refused(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    response = agent_client.post("/runs", json={"email_text": ""})

    assert response.status_code == 422


def test_list_can_filter_by_status(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    post_email(agent_client)

    waiting = agent_client.get("/runs?status=waiting_for_approval").json()
    approved = agent_client.get("/runs?status=approved").json()

    assert len(waiting) == 1
    assert approved == []


def test_approve_decision_approves_the_order(agent_client, monkeypatch):
    calls = install_fakes(monkeypatch)
    post_email(agent_client)

    response = agent_client.post("/runs/1/decision", json={"decision": "approve"})

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert calls["approve"] == [7]


def test_reject_decision_does_not_approve(agent_client, monkeypatch):
    calls = install_fakes(monkeypatch)
    post_email(agent_client)

    response = agent_client.post("/runs/1/decision", json={"decision": "reject"})

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert calls["approve"] == []


def test_second_decision_is_refused(agent_client, monkeypatch):
    calls = install_fakes(monkeypatch)
    post_email(agent_client)
    agent_client.post("/runs/1/decision", json={"decision": "approve"})

    response = agent_client.post("/runs/1/decision", json={"decision": "approve"})

    assert response.status_code == 409
    assert calls["approve"] == [7]


def test_decision_for_unknown_run_is_404(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    response = agent_client.post("/runs/99/decision", json={"decision": "approve"})

    assert response.status_code == 404


def test_decision_must_be_approve_or_reject(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    post_email(agent_client)

    response = agent_client.post("/runs/1/decision", json={"decision": "maybe"})

    assert response.status_code == 422


def test_email_with_a_problem_needs_review_and_creates_nothing(agent_client, monkeypatch):
    calls = install_fakes(monkeypatch, match_function=fake_match_with_problem)

    response = post_email(agent_client)

    body = response.json()
    assert body["status"] == "needs_review"
    assert "gold bars" in body["problems"]
    assert body["draft_order_id"] is None
    assert calls["create"] == []


def test_a_crash_is_saved_as_an_error_and_the_email_is_kept(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    def fake_extract_crashes(email_text):
        raise RuntimeError("ERP is down")

    monkeypatch.setattr("agent.nodes.extract_order", fake_extract_crashes)

    response = post_email(agent_client)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "error"
    assert "ERP is down" in body["problems"]
    assert body["email_text"] == "any email"


def test_detail_shows_what_the_agent_understood(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    post_email(agent_client)

    response = agent_client.get("/runs/1")

    assert response.status_code == 200
    understood = response.json()["understood"]
    assert understood["customer_name"] == "Gupta Stores"
    assert understood["lines"][0]["product_id"] == 1


def test_detail_for_unknown_run_is_404(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    response = agent_client.get("/runs/99")

    assert response.status_code == 404