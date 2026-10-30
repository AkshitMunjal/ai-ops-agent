def test_list_products_returns_three_products(client):
    response = client.get("/products")
    products = response.json()

    assert response.status_code == 200
    assert len(products) == 3


def test_low_stock_returns_only_pvc_pipe(client):
    response = client.get("/products/low-stock")
    low_stock_products = response.json()

    assert response.status_code == 200
    assert len(low_stock_products) == 1

    first_product = low_stock_products[0]

    assert first_product["name"] == "PVC Pipe 1 inch (3m)"


def test_get_one_product_returns_steel_bolts(client):
    response = client.get("/products/1")
    product = response.json()

    assert response.status_code == 200
    assert product["name"] == "Steel Bolts M8 (box of 100)"


def test_get_missing_product_returns_404(client):
    response = client.get("/products/99")

    assert response.status_code == 404

def test_search_products_by_name_finds_pvc_pipe(client):
    response = client.get("/products", params={"name": "pipe"})
    products = response.json()
    first_product = products[0]

    assert response.status_code == 200
    assert len(products) == 1
    assert first_product["name"] == "PVC Pipe 1 inch (3m)"


def test_search_products_with_no_match_returns_empty_list(client):
    response = client.get("/products", params={"name": "nothing"})
    products = response.json()

    assert response.status_code == 200
    assert len(products) == 0