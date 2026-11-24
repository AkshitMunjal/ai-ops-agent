import httpx
import pytest

from jobs.stock_check import StockCheckError, run_stock_check
from mcp_server import tools
from tests.test_mcp_permissions import read_audit_rows


def make_product(product_id, stock_quantity, reorder_level, supplier_id):
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "stock_quantity": stock_quantity,
        "reorder_level": reorder_level,
        "supplier_id": supplier_id,
    }


def install_fakes(monkeypatch, low_stock_products, reorders_by_status):
    saved_calls = []

    def fake_get_low_stock_products():
        return low_stock_products

    def fake_get_purchase_orders(status):
        return reorders_by_status.get(status, [])

    def fake_create_purchase_order(supplier_id, lines):
        saved_calls.append({"supplier_id": supplier_id, "lines": lines})
        return {"id": 100 + supplier_id, "status": "draft"}

    monkeypatch.setattr(tools, "get_low_stock_products", fake_get_low_stock_products)
    monkeypatch.setattr(tools, "get_purchase_orders", fake_get_purchase_orders)
    monkeypatch.setattr(tools, "create_purchase_order", fake_create_purchase_order)

    return saved_calls


def test_creates_one_draft_reorder_per_supplier(client, monkeypatch):
    products = [make_product(1, 5, 20, 1), make_product(2, 0, 10, 1), make_product(4, 3, 5, 2)]
    saved_calls = install_fakes(monkeypatch, products, {})

    outcome = run_stock_check()

    assert len(outcome["created"]) == 2
    assert outcome["failed"] == []
    assert saved_calls[0]["supplier_id"] == 1
    assert len(saved_calls[0]["lines"]) == 2
    assert saved_calls[1] == {"supplier_id": 2, "lines": [{"product_id": 4, "quantity": 7}]}


def test_products_already_in_a_draft_are_not_ordered_again(client, monkeypatch):
    products = [make_product(3, 2, 5, 2), make_product(4, 3, 5, 2)]
    drafts = [{"id": 9, "lines": [{"product_id": 3, "product_name": "Ink", "quantity": 8}]}]
    saved_calls = install_fakes(monkeypatch, products, {"draft": drafts})

    run_stock_check()

    assert saved_calls == [{"supplier_id": 2, "lines": [{"product_id": 4, "quantity": 7}]}]


def test_products_in_an_approved_reorder_are_not_ordered_again(client, monkeypatch):
    products = [make_product(3, 2, 5, 2), make_product(4, 3, 5, 2)]
    approved = [{"id": 9, "lines": [{"product_id": 3, "product_name": "Ink", "quantity": 8}]}]
    saved_calls = install_fakes(monkeypatch, products, {"approved": approved})

    run_stock_check()

    assert saved_calls == [{"supplier_id": 2, "lines": [{"product_id": 4, "quantity": 7}]}]


def test_nothing_low_means_no_drafts(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [], {})

    outcome = run_stock_check()

    assert outcome == {"created": [], "failed": []}
    assert saved_calls == []


def test_one_supplier_failing_does_not_stop_the_others(client, monkeypatch):
    products = [make_product(1, 5, 20, 1), make_product(4, 3, 5, 2)]
    saved_calls = install_fakes(monkeypatch, products, {})

    def fake_create_with_one_refusal(supplier_id, lines):
        if supplier_id == 1:
            request = httpx.Request("POST", "http://test/purchase-orders")
            response = httpx.Response(400, json={"detail": "refused"}, request=request)
            raise httpx.HTTPStatusError("bad request", request=request, response=response)

        saved_calls.append({"supplier_id": supplier_id, "lines": lines})
        return {"id": 102, "status": "draft"}

    monkeypatch.setattr(tools, "create_purchase_order", fake_create_with_one_refusal)

    outcome = run_stock_check()

    assert len(outcome["created"]) == 1
    assert len(outcome["failed"]) == 1
    assert outcome["failed"][0]["supplier_id"] == 1
    assert "refused" in outcome["failed"][0]["reason"]


def test_erp_down_stops_the_job_with_a_clear_error(client, monkeypatch):
    saved_calls = install_fakes(monkeypatch, [], {})

    def erp_is_down():
        raise httpx.ConnectError("down")

    monkeypatch.setattr(tools, "get_low_stock_products", erp_is_down)

    with pytest.raises(StockCheckError) as error_info:
        run_stock_check()

    assert "not reachable" in str(error_info.value)
    assert saved_calls == []


def test_every_step_is_logged_as_the_stock_bot(client, monkeypatch):
    products = [make_product(1, 5, 20, 1)]
    install_fakes(monkeypatch, products, {})

    run_stock_check()
    audit_rows = read_audit_rows()

    tool_names = []
    for audit_row in audit_rows:
        assert audit_row.who == "stock-bot"
        assert audit_row.outcome == "allowed"
        tool_names.append(audit_row.tool_name)

    assert tool_names == ["list_low_stock_products", "list_open_reorders", "create_draft_reorder"]