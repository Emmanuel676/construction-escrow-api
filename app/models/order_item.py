from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.hardware_order import HardwareOrder


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("hardware_orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_ugx: Mapped[int] = mapped_column(BigInteger, nullable=False)
    line_total_ugx: Mapped[int] = mapped_column(BigInteger, nullable=False)

    order: Mapped["HardwareOrder"] = relationship(back_populates="items")
