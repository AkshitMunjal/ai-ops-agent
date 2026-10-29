from datetime import date

from database.models import Customer
from database.models import Invoice
from database.models import Order
from database.models import OrderItem
from database.models import Product
from database.models import Supplier
from database.session import open_session


def seed_sample_data():
    with open_session() as database_session:
        # Part A: customers and suppliers
        sharma_traders = Customer(name="Sharma Traders", email="sharma@example.com")
        gupta_stores = Customer(name="Gupta Stores", email="gupta@example.com")

        hardware_supplier = Supplier(name="Punjab Hardware Supply", email="sales@punjabhardware.example.com")
        pipe_supplier = Supplier(name="Ludhiana Pipes", email="orders@ludhianapipes.example.com")

        database_session.add_all([sharma_traders, gupta_stores, hardware_supplier, pipe_supplier])
        database_session.flush()

        # Part B: products, each pointing to its supplier
        steel_bolts = Product(
            name="Steel Bolts M8 (box of 100)",
            price_in_rupees=450.0,
            stock_quantity=120,
            reorder_level=40,
            supplier_id=hardware_supplier.id,
        )

        copper_wire = Product(
            name="Copper Wire 2.5mm (90m roll)",
            price_in_rupees=2800.0,
            stock_quantity=35,
            reorder_level=10,
            supplier_id=hardware_supplier.id,
        )

        pvc_pipe = Product(
            name="PVC Pipe 1 inch (3m)",
            price_in_rupees=210.0,
            stock_quantity=15,
            reorder_level=20,
            supplier_id=pipe_supplier.id,
        )

        database_session.add_all([steel_bolts, copper_wire, pvc_pipe])
        database_session.flush()

        # Part C: one approved order with two lines
        gupta_order = Order(customer_id=gupta_stores.id, status="approved")
        database_session.add(gupta_order)
        database_session.flush()

        bolts_line = OrderItem(
            order_id=gupta_order.id,
            product_id=steel_bolts.id,
            quantity=10,
            unit_price_in_rupees=450.0,
        )

        wire_line = OrderItem(
            order_id=gupta_order.id,
            product_id=copper_wire.id,
            quantity=2,
            unit_price_in_rupees=2800.0,
        )

        database_session.add_all([bolts_line, wire_line])

        # Part D: one unpaid invoice for that order, already overdue
        gupta_invoice = Invoice(
            order_id=gupta_order.id,
            amount_in_rupees=10100.0,
            due_date=date(2026, 10, 15),
            status="unpaid",
        )

        database_session.add(gupta_invoice)

        database_session.commit()

    print("Sample data saved")


if __name__ == "__main__":
    seed_sample_data()