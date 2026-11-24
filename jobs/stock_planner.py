def make_reorder_plans(low_stock_products, already_ordered_product_ids):
    lines_by_supplier = {}

    for product in low_stock_products:
        product_id = product["id"]

        if product_id in already_ordered_product_ids:
            continue

        target_stock = product["reorder_level"] * 2
        quantity_to_order = target_stock - product["stock_quantity"]

        if quantity_to_order <= 0:
            continue

        line = {"product_id": product_id, "quantity": quantity_to_order}
        supplier_id = product["supplier_id"]

        if supplier_id not in lines_by_supplier:
            lines_by_supplier[supplier_id] = []

        lines_by_supplier[supplier_id].append(line)

    plans = []

    for supplier_id, lines in lines_by_supplier.items():
        plan = {"supplier_id": supplier_id, "lines": lines}
        plans.append(plan)

    return plans