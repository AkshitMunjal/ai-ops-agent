from pydantic import BaseModel, Field


class ExtractedLine(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)


class ExtractedOrder(BaseModel):
    customer_name: str
    lines: list[ExtractedLine] = Field(min_length=1)


class MatchedLine(BaseModel):
    product_id: int
    product_name: str
    quantity: int


class MatchedOrder(BaseModel):
    customer_id: int | None
    customer_name: str | None
    lines: list[MatchedLine]
    problems: list[str]

    def is_ready(self):
        has_customer = self.customer_id is not None
        has_no_problems = len(self.problems) == 0
        return has_customer and has_no_problems