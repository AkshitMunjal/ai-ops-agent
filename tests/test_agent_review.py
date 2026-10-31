from tests.test_agent_api import agent_client, post_email  # noqa: F401
from tests.test_agent_graph import fake_match_with_problem, install_fakes


def test_a_run_that_needs_review_can_be_dismissed(agent_client, monkeypatch):
    install_fakes(monkeypatch, match_function=fake_match_with_problem)
    post_email(agent_client)

    response = agent_client.post("/runs/1/dismiss")

    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"


def test_a_dismissed_run_leaves_the_review_list(agent_client, monkeypatch):
    install_fakes(monkeypatch, match_function=fake_match_with_problem)
    post_email(agent_client)
    agent_client.post("/runs/1/dismiss")

    still_waiting_for_review = agent_client.get("/runs?status=needs_review").json()

    assert still_waiting_for_review == []


def test_a_crashed_run_can_be_dismissed(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    def fake_extract_crashes(email_text):
        raise RuntimeError("ERP is down")

    monkeypatch.setattr("agent.nodes.extract_order", fake_extract_crashes)
    post_email(agent_client)

    response = agent_client.post("/runs/1/dismiss")

    assert response.status_code == 200
    assert response.json()["status"] == "dismissed"


def test_a_run_waiting_for_approval_cannot_be_dismissed(agent_client, monkeypatch):
    install_fakes(monkeypatch)
    post_email(agent_client)

    response = agent_client.post("/runs/1/dismiss")

    assert response.status_code == 409


def test_dismissing_an_unknown_run_is_404(agent_client, monkeypatch):
    install_fakes(monkeypatch)

    response = agent_client.post("/runs/99/dismiss")

    assert response.status_code == 404