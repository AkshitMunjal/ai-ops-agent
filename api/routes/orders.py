from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from api.schemas import NewOrder
from database.models import Customer
from database.models import Order
from database.models import OrderItem
from database.models import Product
from database.session import open_session

router = APIRouter()


@router.post("/orders", status_code=201)
def create_draft_order(new_order: NewOrder):
    if len(new_order.lines) == 0:
        raise HTTPException(status_code=400, detail="Order needs at least one line")

    with open_session() as database_session:
        customer = database_session.get(Customer, new_order.customer_id)

        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        order_to_save = Order(customer_id=customer.id)
        database_session.add(order_to_save)
        database_session.flush()

        for line in new_order.lines:
            product = database_session.get(Product, line.product_id)

            if product is None:
                raise HTTPException(status_code=404, detail="Product not found")

            order_line = OrderItem(
                order_id=order_to_save.id,
                product_id=product.id,
                quantity=line.quantity,
                unit_price_in_rupees=product.price_in_rupees,
            )
            database_session.add(order_line)

        database_session.commit()

        saved_order_id = order_to_save.id
        saved_order_status = order_to_save.status

    return {"id": saved_order_id, "status": saved_order_status}


@router.get("/orders/{order_id}")
def get_one_order(order_id: int):
    with open_session() as database_session:
        order = database_session.get(Order, order_id)

        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        customer = database_session.get(Customer, order.customer_id)

        select_lines = select(OrderItem)
        select_lines = select_lines.where(OrderItem.order_id == order.id)
        order_lines = database_session.scalars(select_lines)

        lines_as_dictionaries = []
        order_total = 0

        for line in order_lines:
            product = database_session.get(Product, line.product_id)
            line_total = line.quantity * line.unit_price_in_rupees
            order_total = order_total + line_total

            line_dictionary = {
                "product_id": product.id,
                "product_name": product.name,
                "quantity": line.quantity,
                "unit_price_in_rupees": line.unit_price_in_rupees,
                "line_total": line_total,
            }
            lines_as_dictionaries.append(line_dictionary)

        order_dictionary = {
            "id": order.id,
            "status": order.status,
            "customer_name": customer.name,
            "lines": lines_as_dictionaries,
            "order_total": order_total,
        }

    return order_dictionary


@router.post("/orders/{order_id}/approve")
def approve_order(order_id: int):
    with open_session() as database_session:
        order = database_session.get(Order, order_id)

        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != "draft":
            raise HTTPException(status_code=409, detail="Only draft orders can be approved")

        order.status = "approved"
        database_session.commit()

        approved_order_id = order.id
        approved_order_status = order.status

    return {"id": approved_order_id, "status": approved_order_status}