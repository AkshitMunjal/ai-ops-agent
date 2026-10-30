from pydantic import BaseModel
from pydantic import Field


class NewCustomer(BaseModel):
    name: str
    email: str


class NewOrderLine(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class NewOrder(BaseModel):
    customer_id: int
    lines: list[NewOrderLine]