from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import NonEmptyStr


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    product_name: NonEmptyStr
    quantity: int = Field(gt=0)
    unit_price_ugx: int = Field(gt=0)


class OrderCreate(BaseModel):
    contractor_id: int = Field(gt=0)
    delivery_site_location: NonEmptyStr
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price_ugx: int
    line_total_ugx: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contractor_id: int
    delivery_site_location: str
    total_amount_ugx: int
    status: str
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime
