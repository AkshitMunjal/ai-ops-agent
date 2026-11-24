import httpx

from ui import erp_client


def make_response(method, body):
    request = httpx.Request(method, "http://test/purchase-orders")
    return httpx.Response(200, json=body, request=request)


def test_get_approved_reorders_asks_only_for_approved(monkeypatch):
    asked = {}

    def fake_get(url, params=None):
        asked["params"] = params
        return make_response("GET", [{"id": 1, "status": "approved"}])

    monkeypatch.setattr(httpx, "get", fake_get)

    approved_reorders = erp_client.get_approved_reorders()

    assert approved_reorders == [{"id": 1, "status": "approved"}]
    assert asked["params"] == {"status": "approved"}


def test_receive_calls_the_receive_address(monkeypatch):
    called_urls = []

    def fake_post(url):
        called_urls.append(url)
        return make_response("POST", {"id": 3, "status": "received"})

    monkeypatch.setattr(httpx, "post", fake_post)

    erp_client.receive_reorder(3)

    assert called_urls[0].endswith("/purchase-orders/3/receive")