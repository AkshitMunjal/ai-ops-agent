from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from database.models import Product
from database.session import open_session

router = APIRouter()


def product_to_dictionary(product):
    return {
        "id": product.id,
        "name": product.name,
        "price_in_rupees": product.price_in_rupees,
        "stock_quantity": product.stock_quantity,
        "reorder_level": product.reorder_level,
        "supplier_id": product.supplier_id,
    }


@router.get("/products")
def list_products():
    select_all_products = select(Product)
    products_as_dictionaries = []

    with open_session() as database_session:
        product_rows = database_session.scalars(select_all_products)

        for product in product_rows:
            product_dictionary = product_to_dictionary(product)
            products_as_dictionaries.append(product_dictionary)

    return products_as_dictionaries


@router.get("/products/low-stock")
def list_low_stock_products():
    low_stock_condition = Product.stock_quantity <= Product.reorder_level

    select_low_stock = select(Product)
    select_low_stock = select_low_stock.where(low_stock_condition)

    low_stock_as_dictionaries = []

    with open_session() as database_session:
        product_rows = database_session.scalars(select_low_stock)

        for product in product_rows:
            product_dictionary = product_to_dictionary(product)
            low_stock_as_dictionaries.append(product_dictionary)

    return low_stock_as_dictionaries


@router.get("/products/{product_id}")
def get_one_product(product_id: int):
    with open_session() as database_session:
        product = database_session.get(Product, product_id)

        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        product_dictionary = product_to_dictionary(product)

    return product_dictionary