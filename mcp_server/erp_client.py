import os

import httpx

erp_api_url = os.environ.get("ERP_API_URL", "http://127.0.0.1:8000")


def search_customers(name):
    response = httpx.get(erp_api_url + "/customers", params={"name": name})
    response.raise_for_status()
    customers = response.json()
    return customers

def search_products(name):
    response = httpx.get(erp_api_url + "/products", params={"name": name})
    response.raise_for_status()
    products = response.json()
    return products

def get_low_stock_products():
    response = httpx.get(erp_api_url + "/products/low-stock")
    response.raise_for_status()
    products = response.json()
    return products


def get_overdue_invoices():
    response = httpx.get(erp_api_url + "/invoices/overdue")
    response.raise_for_status()
    invoices = response.json()
    return invoices


def get_order_by_id(order_id):
    response = httpx.get(erp_api_url + "/orders/" + str(order_id))
    response.raise_for_status()
    order = response.json()
    return order


def get_invoice_by_id(invoice_id):
    response = httpx.get(erp_api_url + "/invoices/" + str(invoice_id))
    response.raise_for_status()
    invoice = response.json()
    return invoice

def create_order(customer_id, lines):
    order_body = {"customer_id": customer_id, "lines": lines}
    response = httpx.post(erp_api_url + "/orders", json=order_body)
    response.raise_for_status()
    created_order = response.json()
    return created_order

def mark_paid_in_erp(invoice_id):
    response = httpx.post(erp_api_url + "/invoices/" + str(invoice_id) + "/mark-paid")
    response.raise_for_status()
    paid_invoice = response.json()
    return paid_invoice