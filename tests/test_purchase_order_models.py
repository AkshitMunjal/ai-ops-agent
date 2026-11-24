from sqlalchemy import select

from database.models import PurchaseOrder, PurchaseOrderItem
from database.session import open_session


def test_a_new_purchase_order_is_a_draft_and_keeps_its_items(client):
    with open_session() as database_session:
        purchase_order = PurchaseOrder(supplier_id=1)
        database_session.add(purchase_order)
        database_session.flush()

        order_item = PurchaseOrderItem(
            purchase_order_id=purchase_order.id,
            product_id=1,
            quantity=35,
        )
        database_session.add(order_item)
        database_session.commit()

        saved_id = purchase_order.id

    with open_session() as database_session:
        saved_order = database_session.get(PurchaseOrder, saved_id)

        select_items = select(PurchaseOrderItem)
        select_items = select_items.where(PurchaseOrderItem.purchase_order_id == saved_id)
        saved_items = list(database_session.scalars(select_items))

    assert saved_order.status == "draft"
    assert saved_order.supplier_id == 1
    assert len(saved_items) == 1
    assert saved_items[0].quantity == 35