from database.models import Product, Supplier
from database.session import open_session


def make_second_supplier_with_a_product():
    with open_session() as database_session:
        other_supplier = Supplier(name="Wire Co", email="wire@example.com")
        database_session.add(other_supplier)
        database_session.flush()

        other_product = Product(
            name="Copper Wire Test",
            price_in_rupees=2800.0,
            stock_quantity=3,
            reorder_level=10,
            supplier_id=other_supplier.id,
        )
        database_session.add(other_product)
        database_session.commit()

        return other_supplier.id, other_product.id


def post_purchase_order(client, supplier_id, product_id, quantity=35):
    new_order = {"supplier_id": supplier_id, "lines": [{"product_id": product_id, "quantity": quantity}]}
    return client.post("/purchase-orders", json=new_order)


def supplier_id_of(product_id):
    with open_session() as database_session:
        product = database_session.get(Product, product_id)
        return product.supplier_id


def test_create_draft_purchase_order_returns_201_and_draft_status(client):
    response = post_purchase_order(client, supplier_id_of(1), 1)

    assert response.status_code == 201
    assert response.json()["status"] == "draft"
    assert response.json()["id"] == 1


def test_a_saved_purchase_order_shows_its_supplier_and_lines(client):
    post_purchase_order(client, supplier_id_of(1), 1, quantity=35)

    response = client.get("/purchase-orders/1")
    purchase_order = response.json()

    assert response.status_code == 200
    assert purchase_order["status"] == "draft"
    assert purchase_order["supplier_id"] == supplier_id_of(1)
    assert len(purchase_order["lines"]) == 1
    assert purchase_order["lines"][0]["product_id"] == 1
    assert purchase_order["lines"][0]["quantity"] == 35


def test_purchase_order_with_no_lines_is_refused(client):
    response = client.post("/purchase-orders", json={"supplier_id": 1, "lines": []})

    assert response.status_code == 400


def test_purchase_order_with_zero_quantity_is_refused(client):
    response = post_purchase_order(client, supplier_id_of(1), 1, quantity=0)

    assert response.status_code == 422


def test_purchase_order_for_unknown_supplier_is_refused(client):
    response = post_purchase_order(client, 99, 1)

    assert response.status_code == 404


def test_purchase_order_with_unknown_product_is_refused_and_nothing_is_saved(client):
    response = post_purchase_order(client, supplier_id_of(1), 99)

    assert response.status_code == 404
    assert client.get("/purchase-orders").json() == []


def test_product_from_another_supplier_is_refused_and_nothing_is_saved(client):
    other_supplier_id, other_product_id = make_second_supplier_with_a_product()

    response = post_purchase_order(client, supplier_id_of(1), other_product_id)

    assert response.status_code == 400
    assert client.get("/purchase-orders").json() == []


def test_the_list_can_be_filtered_by_status(client):
    post_purchase_order(client, supplier_id_of(1), 1)
    post_purchase_order(client, supplier_id_of(2), 2)
    client.post("/purchase-orders/2/cancel")

    all_orders = client.get("/purchase-orders").json()
    draft_orders = client.get("/purchase-orders", params={"status": "draft"}).json()

    assert len(all_orders) == 2
    assert len(draft_orders) == 1
    assert draft_orders[0]["id"] == 1


def test_approving_a_draft_purchase_order_changes_it(client):
    post_purchase_order(client, supplier_id_of(1), 1)

    response = client.post("/purchase-orders/1/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/purchase-orders/1").json()["status"] == "approved"


def test_an_approved_purchase_order_cannot_be_approved_or_cancelled_again(client):
    post_purchase_order(client, supplier_id_of(1), 1)
    client.post("/purchase-orders/1/approve")

    approve_again = client.post("/purchase-orders/1/approve")
    cancel_after = client.post("/purchase-orders/1/cancel")

    assert approve_again.status_code == 409
    assert cancel_after.status_code == 409


def test_cancelling_a_draft_purchase_order_changes_it(client):
    post_purchase_order(client, supplier_id_of(1), 1)

    response = client.post("/purchase-orders/1/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get("/purchase-orders/1").json()["status"] == "cancelled"


def test_a_cancelled_purchase_order_cannot_be_approved_or_cancelled_again(client):
    post_purchase_order(client, supplier_id_of(1), 1)
    client.post("/purchase-orders/1/cancel")

    approve_after = client.post("/purchase-orders/1/approve")
    cancel_again = client.post("/purchase-orders/1/cancel")

    assert approve_after.status_code == 409
    assert cancel_again.status_code == 409


def test_a_missing_purchase_order_returns_404(client):
    assert client.get("/purchase-orders/99").status_code == 404
    assert client.post("/purchase-orders/99/approve").status_code == 404
    assert client.post("/purchase-orders/99/cancel").status_code == 404