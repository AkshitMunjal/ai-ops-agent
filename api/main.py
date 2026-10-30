from fastapi import FastAPI

from api.routes import customers
from api.routes import invoices
from api.routes import orders
from api.routes import products

app = FastAPI(title="ERP API")

app.include_router(customers.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(invoices.router)