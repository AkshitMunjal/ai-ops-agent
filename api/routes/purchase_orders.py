from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from api.schemas import NewPurchaseOrder
from database.models import Product
from database.models import PurchaseOrder
from database.models import PurchaseOrderItem
from database.models import Supplier
from database.session import open_session

router = APIRouter()


def describe_purchase_order(database_session, purchase_order):
    supplier = database_session.get(Supplier, purchase_order.supplier_id)

    select_items = select(PurchaseOrderItem)
    select_items = select_items.where(PurchaseOrderItem.purchase_order_id == purchase_order.id)
    order_items = database_session.scalars(select_items)

    lines_as_dictionaries = []
    for order_item in order_items:
        product = database_session.get(Product, order_item.product_id)

        line_dictionary = {
            "product_id": product.id,
            "product_name": product.name,
            "quantity": order_item.quantity,
        }
        lines_as_dictionaries.append(line_dictionary)

    return {
        "id": purchase_order.id,
        "status": purchase_order.status,
        "supplier_id": supplier.id,
        "supplier_name": supplier.name,
        "lines": lines_as_dictionaries,
    }


def change_draft_status(purchase_order_id, new_status, action_word):
    with open_session() as database_session:
        purchase_order = database_session.get(PurchaseOrder, purchase_order_id)

        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if purchase_order.status != "draft":
            raise HTTPException(status_code=409, detail=f"Only draft purchase orders can be {action_word}")

        purchase_order.status = new_status
        database_session.commit()

        changed_id = purchase_order.id
        changed_status = purchase_order.status

    return {"id": changed_id, "status": changed_status}


@router.post("/purchase-orders", status_code=201)
def create_draft_purchase_order(new_purchase_order: NewPurchaseOrder):
    if len(new_purchase_order.lines) == 0:
        raise HTTPException(status_code=400, detail="Purchase order needs at least one line")

    with open_session() as database_session:
        supplier = database_session.get(Supplier, new_purchase_order.supplier_id)

        if supplier is None:
            raise HTTPException(status_code=404, detail="Supplier not found")

        order_to_save = PurchaseOrder(supplier_id=supplier.id)
        database_session.add(order_to_save)
        database_session.flush()

        for line in new_purchase_order.lines:
            product = database_session.get(Product, line.product_id)

            if product is None:
                raise HTTPException(status_code=404, detail="Product not found")

            if product.supplier_id != supplier.id:
                raise HTTPException(status_code=400, detail="Product does not belong to this supplier")

            order_item = PurchaseOrderItem(
                purchase_order_id=order_to_save.id,
                product_id=product.id,
                quantity=line.quantity,
            )
            database_session.add(order_item)

        database_session.commit()

        saved_order_id = order_to_save.id
        saved_order_status = order_to_save.status

    return {"id": saved_order_id, "status": saved_order_status}


@router.get("/purchase-orders")
def list_purchase_orders(status: str | None = None):
    select_orders = select(PurchaseOrder).order_by(PurchaseOrder.id)

    if status is not None:
        select_orders = select_orders.where(PurchaseOrder.status == status)

    with open_session() as database_session:
        found_orders = database_session.scalars(select_orders).all()

        orders_as_dictionaries = []
        for purchase_order in found_orders:
            order_dictionary = describe_purchase_order(database_session, purchase_order)
            orders_as_dictionaries.append(order_dictionary)

    return orders_as_dictionaries


@router.get("/purchase-orders/{purchase_order_id}")
def get_one_purchase_order(purchase_order_id: int):
    with open_session() as database_session:
        purchase_order = database_session.get(PurchaseOrder, purchase_order_id)

        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        order_dictionary = describe_purchase_order(database_session, purchase_order)

    return order_dictionary


@router.post("/purchase-orders/{purchase_order_id}/approve")
def approve_purchase_order(purchase_order_id: int):
    return change_draft_status(purchase_order_id, "approved", "approved")


@router.post("/purchase-orders/{purchase_order_id}/cancel")
def cancel_purchase_order(purchase_order_id: int):
    return change_draft_status(purchase_order_id, "cancelled", "cancelled")


@router.post("/purchase-orders/{purchase_order_id}/receive")
def receive_purchase_order(purchase_order_id: int):
    with open_session() as database_session:
        purchase_order = database_session.get(PurchaseOrder, purchase_order_id)

        if purchase_order is None:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        if purchase_order.status != "approved":
            raise HTTPException(status_code=409, detail="Only approved purchase orders can be received")

        select_items = select(PurchaseOrderItem)
        select_items = select_items.where(PurchaseOrderItem.purchase_order_id == purchase_order.id)
        order_items = database_session.scalars(select_items).all()

        for order_item in order_items:
            product = database_session.get(Product, order_item.product_id)
            product.stock_quantity = product.stock_quantity + order_item.quantity

        purchase_order.status = "received"
        database_session.commit()

        changed_id = purchase_order.id
        changed_status = purchase_order.status

    return {"id": changed_id, "status": changed_status}