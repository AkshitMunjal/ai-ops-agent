from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from agent_api.database import Base, database_engine, open_session
from cost_control.limit import SpendLimitReached, check_spend_limit, get_daily_limit, spent_today
from cost_control.models import LlmUsage
from cost_control.recorder import record_usage
from extraction import llm_client


@pytest.fixture
def usage_table(monkeypatch):
    Base.metadata.drop_all(database_engine)
    Base.metadata.create_all(database_engine)
    monkeypatch.delenv("DAILY_SPEND_LIMIT_USD", raising=False)


def add_usage(cost, days_ago=0):
    usage_row = LlmUsage(model="test", cost=cost, created_at=datetime.now() - timedelta(days=days_ago))

    with open_session() as database_session:
        database_session.add(usage_row)
        database_session.commit()


def all_usage_rows():
    with open_session() as database_session:
        found_rows = database_session.scalars(select(LlmUsage))
        return found_rows.all()


def test_record_usage_saves_tokens_and_cost(usage_table):
    record_usage("some/model", {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0004})

    row = all_usage_rows()[0]
    assert row.model == "some/model"
    assert row.prompt_tokens == 100
    assert row.completion_tokens == 20
    assert row.cost == pytest.approx(0.0004)


def test_record_usage_without_a_cost_saves_zero(usage_table):
    record_usage("free/model", {"prompt_tokens": 5})

    assert all_usage_rows()[0].cost == 0.0


def test_an_empty_day_has_zero_spending(usage_table):
    assert spent_today() == 0.0


def test_spent_today_adds_todays_calls_and_ignores_yesterday(usage_table):
    add_usage(0.2)
    add_usage(0.3)
    add_usage(5.0, days_ago=1)

    assert spent_today() == pytest.approx(0.5)


def test_the_default_daily_limit_is_one_dollar(usage_table):
    assert get_daily_limit() == 1.0


def test_the_daily_limit_can_be_set_in_the_environment(usage_table, monkeypatch):
    monkeypatch.setenv("DAILY_SPEND_LIMIT_USD", "0.25")

    assert get_daily_limit() == 0.25


def test_spending_under_the_limit_is_allowed(usage_table):
    add_usage(0.99)

    check_spend_limit()


def test_spending_at_the_limit_is_refused(usage_table):
    add_usage(1.0)

    with pytest.raises(SpendLimitReached):
        check_spend_limit()


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "choices": [{"message": {"content": "OK"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.0004},
        }


@pytest.fixture
def fake_llm(usage_table, monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "post", fake_post)
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("OPENROUTER_MODEL", "some/model")
    return calls


def test_ask_llm_returns_the_answer_and_saves_the_usage(fake_llm):
    answer = llm_client.ask_llm("instruction", "email")

    assert answer == "OK"
    assert spent_today() == pytest.approx(0.0004)


def test_ask_llm_refuses_at_the_limit_without_calling_the_llm(fake_llm):
    add_usage(2.0)

    with pytest.raises(SpendLimitReached):
        llm_client.ask_llm("instruction", "email")

    assert fake_llm == []


def test_ask_llm_still_answers_if_saving_the_usage_fails(fake_llm, monkeypatch):
    def broken_recorder(model_name, usage):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(llm_client, "record_usage", broken_recorder)

    assert llm_client.ask_llm("instruction", "email") == "OK"