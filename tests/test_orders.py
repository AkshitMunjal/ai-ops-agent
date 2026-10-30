def test_create_draft_order_returns_201_and_draft_status(client):
    new_order = {"customer_id": 1, "lines": [{"product_id": 3, "quantity": 5}]}
    response = client.post("/orders", json=new_order)
    created_order = response.json()

    assert response.status_code == 201
    assert created_order["status"] == "draft"
    assert created_order["id"] == 2


def test_order_with_zero_quantity_is_refused_and_not_saved(client):
    bad_order = {"customer_id": 1, "lines": [{"product_id": 3, "quantity": 0}]}
    response = client.post("/orders", json=bad_order)

    assert response.status_code == 422

    check_response = client.get("/orders/2")

    assert check_response.status_code == 404


def test_order_for_unknown_customer_is_refused(client):
    bad_order = {"customer_id": 99, "lines": [{"product_id": 3, "quantity": 5}]}
    response = client.post("/orders", json=bad_order)

    assert response.status_code == 404


def test_order_with_unknown_product_is_refused_and_nothing_is_saved(client):
    bad_order = {"customer_id": 1, "lines": [{"product_id": 99, "quantity": 5}]}
    response = client.post("/orders", json=bad_order)

    assert response.status_code == 404

    check_response = client.get("/orders/2")

    assert check_response.status_code == 404


def test_order_with_no_lines_is_refused(client):
    bad_order = {"customer_id": 1, "lines": []}
    response = client.post("/orders", json=bad_order)

    assert response.status_code == 400


def test_caller_cannot_set_the_price(client):
    sneaky_order = {
        "customer_id": 1,
        "lines": [{"product_id": 3, "quantity": 5, "unit_price_in_rupees": 1.0}],
    }
    client.post("/orders", json=sneaky_order)

    read_response = client.get("/orders/2")
    saved_order = read_response.json()

    assert saved_order["order_total"] == 1050.0


def test_get_seed_order_returns_customer_lines_and_total(client):
    response = client.get("/orders/1")
    order = response.json()
    order_lines = order["lines"]

    assert response.status_code == 200
    assert order["customer_name"] == "Gupta Stores"
    assert order["status"] == "approved"
    assert len(order_lines) == 2
    assert order["order_total"] == 10100.0


def test_get_missing_order_returns_404(client):
    response = client.get("/orders/99")

    assert response.status_code == 404


def test_approving_a_draft_order_changes_the_same_order(client):
    new_order = {"customer_id": 1, "lines": [{"product_id": 3, "quantity": 5}]}
    client.post("/orders", json=new_order)

    approve_response = client.post("/orders/2/approve")
    approved_order = approve_response.json()

    assert approve_response.status_code == 200
    assert approved_order["status"] == "approved"

    read_response = client.get("/orders/2")
    saved_order = read_response.json()

    assert saved_order["status"] == "approved"


def test_approving_the_same_order_twice_is_refused(client):
    new_order = {"customer_id": 1, "lines": [{"product_id": 3, "quantity": 5}]}
    client.post("/orders", json=new_order)
    client.post("/orders/2/approve")

    second_response = client.post("/orders/2/approve")

    assert second_response.status_code == 409

def test_approving_an_already_approved_order_is_refused(client):
    response = client.post("/orders/1/approve")

    assert response.status_code == 409


def test_approving_a_missing_order_returns_404(client):
    response = client.post("/orders/99/approve")

    assert response.status_code == 404