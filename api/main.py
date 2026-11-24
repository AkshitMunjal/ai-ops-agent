from fastapi import FastAPI

from api.routes import customers
from api.routes import invoices
from api.routes import orders
from api.routes import products
from api.routes import purchase_orders
from api.routes import follow_ups

app = FastAPI(title="ERP API")

app.include_router(customers.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(invoices.router)
app.include_router(purchase_orders.router)
app.include_router(follow_ups.router)