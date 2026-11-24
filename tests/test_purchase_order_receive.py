from sqlalchemy import select

from database.models import Product
from database.session import open_session


def first_product():
    with open_session() as database_session:
        product = database_session.scalars(select(Product).order_by(Product.id)).first()
        return product.id, product.supplier_id


def stock_of(product_id):
    with open_session() as database_session:
        product = database_session.get(Product, product_id)
        return product.stock_quantity


def make_purchase_order(client, quantity=35):
    product_id, supplier_id = first_product()
    new_order = {"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": quantity}]}
    created = client.post("/purchase-orders", json=new_order).json()
    return created["id"], product_id


def test_receiving_an_approved_reorder_adds_the_stock_and_closes_it(client):
    purchase_order_id, product_id = make_purchase_order(client, 35)
    stock_before = stock_of(product_id)
    client.post(f"/purchase-orders/{purchase_order_id}/approve")

    response = client.post(f"/purchase-orders/{purchase_order_id}/receive")

    assert response.status_code == 200
    assert response.json()["status"] == "received"
    assert stock_of(product_id) == stock_before + 35


def test_a_draft_reorder_cannot_be_received(client):
    purchase_order_id, product_id = make_purchase_order(client)
    stock_before = stock_of(product_id)

    response = client.post(f"/purchase-orders/{purchase_order_id}/receive")

    assert response.status_code == 409
    assert stock_of(product_id) == stock_before


def test_a_cancelled_reorder_cannot_be_received(client):
    purchase_order_id, product_id = make_purchase_order(client)
    stock_before = stock_of(product_id)
    client.post(f"/purchase-orders/{purchase_order_id}/cancel")

    response = client.post(f"/purchase-orders/{purchase_order_id}/receive")

    assert response.status_code == 409
    assert stock_of(product_id) == stock_before


def test_a_reorder_can_only_be_received_once(client):
    purchase_order_id, product_id = make_purchase_order(client, 10)
    stock_before = stock_of(product_id)
    client.post(f"/purchase-orders/{purchase_order_id}/approve")
    client.post(f"/purchase-orders/{purchase_order_id}/receive")

    second = client.post(f"/purchase-orders/{purchase_order_id}/receive")

    assert second.status_code == 409
    assert stock_of(product_id) == stock_before + 10


def test_receiving_an_unknown_reorder_is_refused(client):
    response = client.post("/purchase-orders/99999/receive")

    assert response.status_code == 404