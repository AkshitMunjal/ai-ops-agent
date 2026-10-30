def test_list_customers_returns_two_customers(client):
    response = client.get("/customers")
    customers = response.json()

    assert response.status_code == 200
    assert len(customers) == 2


def test_get_one_customer_returns_gupta_stores(client):
    response = client.get("/customers/2")
    customer = response.json()

    assert response.status_code == 200
    assert customer["name"] == "Gupta Stores"


def test_get_missing_customer_returns_404(client):
    response = client.get("/customers/99")

    assert response.status_code == 404


def test_create_customer_returns_201(client):
    new_customer = {"name": "Verma Hardware", "email": "verma@example.com"}
    response = client.post("/customers", json=new_customer)

    assert response.status_code == 201
    assert response.json()["name"] == "Verma Hardware"


def test_create_customer_without_email_is_refused_and_not_saved(client):
    incomplete_customer = {"name": "No Email Co"}
    response = client.post("/customers", json=incomplete_customer)

    assert response.status_code == 422

    list_response = client.get("/customers")
    customers = list_response.json()

    assert len(customers) == 2