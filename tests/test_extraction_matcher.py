from extraction.matcher import match_customer, match_order, match_product
from extraction.schemas import ExtractedOrder

gupta = {"id": 2, "name": "Gupta Stores", "email": "gupta@example.com"}
sharma = {"id": 1, "name": "Sharma Traders", "email": "sharma@example.com"}
bolts = {"id": 1, "name": "Steel Bolts M8 (box of 100)"}
wire = {"id": 2, "name": "Copper Wire 2.5mm (90m roll)"}


def fake_search_returning(rows):
    def fake_search(name):
        return rows

    return fake_search


def fake_product_search(name):
    if "bolts" in name:
        return [bolts]
    if "wire" in name:
        return [wire]
    return []


def fake_customer_search(name):
    if "Gupta" in name:
        return [gupta]
    return []


def test_customer_with_one_match(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_search_returning([gupta]))

    customer, problem = match_customer("Gupta Stores")

    assert customer["id"] == 2
    assert problem is None


def test_customer_with_no_match(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_search_returning([]))

    customer, problem = match_customer("Nobody Ltd")

    assert customer is None
    assert "No customer found" in problem


def test_customer_with_many_matches(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_search_returning([gupta, sharma]))

    customer, problem = match_customer("a")

    assert customer is None
    assert "More than one customer" in problem


def test_product_with_one_match(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_products", fake_search_returning([bolts]))

    product, problem = match_product("steel bolts M8")

    assert product["id"] == 1
    assert problem is None


def test_product_with_no_match(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_products", fake_search_returning([]))

    product, problem = match_product("gold bars")

    assert product is None
    assert "No product found" in problem


def test_product_with_many_matches(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_products", fake_search_returning([bolts, wire]))

    product, problem = match_product("e")

    assert product is None
    assert "More than one product" in problem


def test_good_order_is_ready(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_customer_search)
    monkeypatch.setattr("extraction.matcher.search_products", fake_product_search)
    extracted_order = ExtractedOrder(
        customer_name="Gupta Stores",
        lines=[
            {"product_name": "steel bolts M8", "quantity": 40},
            {"product_name": "copper wire 2.5mm", "quantity": 3},
        ],
    )

    matched_order = match_order(extracted_order)

    assert matched_order.is_ready()
    assert matched_order.customer_id == 2
    assert len(matched_order.lines) == 2
    assert matched_order.lines[0].product_id == 1
    assert matched_order.lines[0].quantity == 40


def test_order_with_unknown_product_is_not_ready(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_customer_search)
    monkeypatch.setattr("extraction.matcher.search_products", fake_product_search)
    extracted_order = ExtractedOrder(
        customer_name="Gupta Stores",
        lines=[
            {"product_name": "steel bolts M8", "quantity": 40},
            {"product_name": "gold bars", "quantity": 2},
        ],
    )

    matched_order = match_order(extracted_order)

    assert not matched_order.is_ready()
    assert len(matched_order.problems) == 1


def test_order_with_unknown_customer_is_not_ready(monkeypatch):
    monkeypatch.setattr("extraction.matcher.search_customers", fake_customer_search)
    monkeypatch.setattr("extraction.matcher.search_products", fake_product_search)
    extracted_order = ExtractedOrder(
        customer_name="Nobody Ltd",
        lines=[{"product_name": "steel bolts M8", "quantity": 40}],
    )

    matched_order = match_order(extracted_order)

    assert not matched_order.is_ready()
    assert matched_order.customer_id is None