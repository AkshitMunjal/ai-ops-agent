def find_ordered_product_ids(draft_reorders):
    ordered_product_ids = []

    for draft_reorder in draft_reorders:
        for line in draft_reorder["lines"]:
            ordered_product_ids.append(line["product_id"])

    return ordered_product_ids