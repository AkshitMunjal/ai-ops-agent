from jobs.draft_reader import find_ordered_product_ids
from jobs.stock_planner import make_reorder_plans


def make_product(product_id, stock_quantity, reorder_level, supplier_id):
    return {
        "id": product_id,
        "name": f"Product {product_id}",
        "stock_quantity": stock_quantity,
        "reorder_level": reorder_level,
        "supplier_id": supplier_id,
    }


def test_quantity_brings_stock_up_to_twice_the_reorder_level():
    products = [make_product(1, 5, 20, 1)]

    plans = make_reorder_plans(products, [])

    assert plans == [{"supplier_id": 1, "lines": [{"product_id": 1, "quantity": 35}]}]


def test_products_of_the_same_supplier_share_one_plan():
    products = [make_product(1, 5, 20, 1), make_product(2, 0, 10, 1), make_product(4, 3, 5, 2)]

    plans = make_reorder_plans(products, [])

    assert len(plans) == 2
    assert plans[0]["supplier_id"] == 1
    assert len(plans[0]["lines"]) == 2
    assert plans[1]["supplier_id"] == 2


def test_products_already_in_a_draft_are_skipped():
    products = [make_product(3, 2, 5, 2), make_product(4, 3, 5, 2)]

    plans = make_reorder_plans(products, [3])

    assert plans == [{"supplier_id": 2, "lines": [{"product_id": 4, "quantity": 7}]}]


def test_nothing_to_order_gives_no_plans():
    assert make_reorder_plans([], []) == []
    assert make_reorder_plans([make_product(1, 0, 0, 1)], []) == []


def test_ordered_product_ids_are_collected_from_all_drafts():
    drafts = [
        {"id": 1, "lines": [{"product_id": 1, "quantity": 5}, {"product_id": 2, "quantity": 5}]},
        {"id": 2, "lines": [{"product_id": 7, "quantity": 5}]},
    ]

    assert find_ordered_product_ids(drafts) == [1, 2, 7]


def test_no_drafts_means_no_ordered_products():
    assert find_ordered_product_ids([]) == []