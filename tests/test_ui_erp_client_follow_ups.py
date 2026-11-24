import httpx
import pytest

from ui import erp_client


def make_response(method, status_code, body):
    request = httpx.Request(method, "http://test/follow-ups")
    return httpx.Response(status_code, json=body, request=request)


def test_get_draft_follow_ups_asks_only_for_drafts(monkeypatch):
    asked = {}

    def fake_get(url, params=None):
        asked["url"] = url
        asked["params"] = params
        return make_response("GET", 200, [{"id": 1, "status": "draft"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    draft_follow_ups = erp_client.get_draft_follow_ups()

    assert draft_follow_ups == [{"id": 1, "status": "draft"}]
    assert asked["url"].endswith("/follow-ups")
    assert asked["params"] == {"status": "draft"}


def test_send_and_cancel_call_the_right_erp_addresses(monkeypatch):
    called_urls = []

    def fake_post(url, timeout=None):
        called_urls.append(url)
        return make_response("POST", 200, {"id": 1, "status": "done"})

    monkeypatch.setattr(httpx, "post", fake_post)

    erp_client.send_follow_up(1)
    erp_client.cancel_follow_up(2)

    assert called_urls[0].endswith("/follow-ups/1/send")
    assert called_urls[1].endswith("/follow-ups/2/cancel")


def test_a_failed_send_is_raised_so_the_page_can_show_it(monkeypatch):
    def fake_post(url, timeout=None):
        return make_response("POST", 502, {"detail": "The email could not be sent"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        erp_client.send_follow_up(1)