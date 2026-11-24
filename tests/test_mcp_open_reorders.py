from mcp_server import tools
from tests.test_mcp_permissions import call_tool_as, list_tool_names

all_keys = [
    "demo-key-reader",
    "demo-key-orders",
    "demo-key-finance",
    "demo-key-stock",
    "demo-key-followup",
    "demo-key-summary",
]


def test_open_reorders_are_the_drafts_plus_the_approved_ones(client, monkeypatch):
    def fake_get_purchase_orders(status):
        return [{"id": 1 if status == "draft" else 2, "status": status}]

    monkeypatch.setattr(tools, "get_purchase_orders", fake_get_purchase_orders)

    result = call_tool_as("demo-key-reader", "list_open_reorders", {})

    statuses = [reorder["status"] for reorder in result.structured_content["result"]]
    assert statuses == ["draft", "approved"]


def test_every_agent_can_read_open_reorders_but_none_can_receive_goods():
    for api_key in all_keys:
        tool_names = list_tool_names(api_key)

        assert "list_open_reorders" in tool_names
        assert "receive_purchase_order" not in tool_names
        assert "receive_reorder" not in tool_names