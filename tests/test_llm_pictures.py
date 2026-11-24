import pytest

from cost_control.limit import SpendLimitReached, spent_today
from extraction import llm_client
from tests.test_cost_control import FakeResponse, add_usage, fake_llm, usage_table


def test_pictures_are_sent_and_the_usage_is_saved(fake_llm, monkeypatch):
    sent = {}

    def spy_post(url, headers=None, json=None, timeout=None):
        sent["body"] = json
        return FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "post", spy_post)

    answer = llm_client.ask_llm_with_pictures("read it", ["data:image/jpeg;base64,AAA"])

    user_parts = sent["body"]["messages"][1]["content"]
    assert answer == "OK"
    assert user_parts[0]["image_url"]["url"] == "data:image/jpeg;base64,AAA"
    assert user_parts[0]["image_url"]["detail"] == "low"
    assert spent_today() == pytest.approx(0.0004)


def test_picture_detail_can_be_changed_in_the_environment(fake_llm, monkeypatch):
    sent = {}

    def spy_post(url, headers=None, json=None, timeout=None):
        sent["body"] = json
        return FakeResponse()

    monkeypatch.setattr(llm_client.httpx, "post", spy_post)
    monkeypatch.setenv("OCR_IMAGE_DETAIL", "high")

    llm_client.ask_llm_with_pictures("read it", ["data:image/jpeg;base64,AAA"])

    user_parts = sent["body"]["messages"][1]["content"]
    assert user_parts[0]["image_url"]["detail"] == "high"


def test_pictures_are_refused_at_the_spend_limit(fake_llm):
    add_usage(2.0)

    with pytest.raises(SpendLimitReached):
        llm_client.ask_llm_with_pictures("read it", ["data:image/jpeg;base64,AAA"])

    assert fake_llm == []