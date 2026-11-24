import httpx
import pytest

from ui import erp_client


def make_response(method, status_code, body):
    request = httpx.Request(method, "http://test/purchase-orders")
    return httpx.Response(status_code, json=body, request=request)


def test_get_draft_reorders_asks_only_for_drafts(monkeypatch):
    asked = {}

    def fake_get(url, params=None):
        asked["url"] = url
        asked["params"] = params
        return make_response("GET", 200, [{"id": 1, "status": "draft"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    draft_reorders = erp_client.get_draft_reorders()

    assert draft_reorders == [{"id": 1, "status": "draft"}]
    assert asked["url"].endswith("/purchase-orders")
    assert asked["params"] == {"status": "draft"}


def test_approve_and_cancel_call_the_right_erp_addresses(monkeypatch):
    called_urls = []

    def fake_post(url):
        called_urls.append(url)
        return make_response("POST", 200, {"id": 1, "status": "done"})

    monkeypatch.setattr(httpx, "post", fake_post)

    erp_client.approve_reorder(1)
    erp_client.cancel_reorder(2)

    assert called_urls[0].endswith("/purchase-orders/1/approve")
    assert called_urls[1].endswith("/purchase-orders/2/cancel")


def test_erp_refusal_is_raised_so_the_page_can_show_it(monkeypatch):
    def fake_post(url):
        return make_response("POST", 409, {"detail": "Only draft purchase orders can be approved"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        erp_client.approve_reorder(1)