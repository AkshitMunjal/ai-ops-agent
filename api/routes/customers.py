from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy import select

from api.schemas import NewCustomer
from database.models import Customer
from database.session import open_session

router = APIRouter()


def customer_to_dictionary(customer):
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
    }


@router.get("/customers")
def list_customers():
    select_all_customers = select(Customer)
    customers_as_dictionaries = []

    with open_session() as database_session:
        customer_rows = database_session.scalars(select_all_customers)

        for customer in customer_rows:
            customer_dictionary = customer_to_dictionary(customer)
            customers_as_dictionaries.append(customer_dictionary)

    return customers_as_dictionaries


@router.get("/customers/{customer_id}")
def get_one_customer(customer_id: int):
    with open_session() as database_session:
        customer = database_session.get(Customer, customer_id)

        if customer is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer_dictionary = customer_to_dictionary(customer)

    return customer_dictionary


@router.post("/customers", status_code=201)
def create_customer(new_customer: NewCustomer):
    customer_to_save = Customer(name=new_customer.name, email=new_customer.email)

    with open_session() as database_session:
        database_session.add(customer_to_save)
        database_session.commit()

        customer_dictionary = customer_to_dictionary(customer_to_save)

    return customer_dictionary