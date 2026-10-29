from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    price_in_rupees: Mapped[float] = mapped_column()
    stock_quantity: Mapped[int] = mapped_column()
    reorder_level: Mapped[int] = mapped_column()
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))