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


class NewPurchaseOrderLine(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class NewPurchaseOrder(BaseModel):
    supplier_id: int
    lines: list[NewPurchaseOrderLine]


class NewFollowUp(BaseModel):
    invoice_id: int
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)