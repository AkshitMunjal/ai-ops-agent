import os

import httpx

erp_api_url = os.environ.get("ERP_API_URL", "http://127.0.0.1:8000")


def get_draft_reorders():
    response = httpx.get(erp_api_url + "/purchase-orders", params={"status": "draft"})
    response.raise_for_status()
    draft_reorders = response.json()
    return draft_reorders


def approve_reorder(purchase_order_id):
    response = httpx.post(erp_api_url + "/purchase-orders/" + str(purchase_order_id) + "/approve")
    response.raise_for_status()
    approved_reorder = response.json()
    return approved_reorder


def cancel_reorder(purchase_order_id):
    response = httpx.post(erp_api_url + "/purchase-orders/" + str(purchase_order_id) + "/cancel")
    response.raise_for_status()
    cancelled_reorder = response.json()
    return cancelled_reorder


def get_draft_follow_ups():
    response = httpx.get(erp_api_url + "/follow-ups", params={"status": "draft"})
    response.raise_for_status()
    draft_follow_ups = response.json()
    return draft_follow_ups


def send_follow_up(follow_up_id):
    response = httpx.post(erp_api_url + "/follow-ups/" + str(follow_up_id) + "/send", timeout=60)
    response.raise_for_status()
    sent_follow_up = response.json()
    return sent_follow_up


def cancel_follow_up(follow_up_id):
    response = httpx.post(erp_api_url + "/follow-ups/" + str(follow_up_id) + "/cancel")
    response.raise_for_status()
    cancelled_follow_up = response.json()
    return cancelled_follow_up


def get_approved_reorders():
    response = httpx.get(erp_api_url + "/purchase-orders", params={"status": "approved"})
    response.raise_for_status()
    approved_reorders = response.json()
    return approved_reorders


def receive_reorder(purchase_order_id):
    response = httpx.post(erp_api_url + "/purchase-orders/" + str(purchase_order_id) + "/receive")
    response.raise_for_status()
    received_reorder = response.json()
    return received_reorder