import httpx

from mcp_server.erp_client import erp_api_url


def approve_order_in_erp(order_id):
    response = httpx.post(erp_api_url + "/orders/" + str(order_id) + "/approve")
    response.raise_for_status()
    approved_order = response.json()
    return approved_order